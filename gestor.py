from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
import html
import io
import json
import mimetypes
import re
import secrets
import threading
import urllib.parse
import unicodedata
import webbrowser
import zipfile

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
UPLOADS = ROOT / 'assets' / 'uploads'
NEWS = ROOT / 'assets' / 'news'
for folder in (DATA, UPLOADS, NEWS):
    folder.mkdir(parents=True, exist_ok=True)

USED_FORM_TOKENS = set()


def load_json(name):
    path = DATA / name
    try:
        value = json.loads(path.read_text(encoding='utf-8'))
        return value if isinstance(value, list) else []
    except Exception:
        return []


def write_json(name, value):
    (DATA / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )


def save_public_data():
    products = load_json('products.json')
    news = load_json('news.json')
    (ROOT / 'js' / 'products.js').write_text(
        'window.MAYEN_PRODUCTS = ' + json.dumps(products, ensure_ascii=False, indent=2) + ';\n',
        encoding='utf-8'
    )
    (ROOT / 'js' / 'news.js').write_text(
        'window.MAYEN_NEWS = ' + json.dumps(news, ensure_ascii=False, indent=2) + ';\n',
        encoding='utf-8'
    )


def slugify(text):
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', text).strip('-') or 'producto'


def parse_multipart(handler):
    content_type = handler.headers.get('Content-Type', '')
    length = int(handler.headers.get('Content-Length', '0') or 0)
    body = handler.rfile.read(length)
    raw = (f'Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n').encode() + body
    message = BytesParser(policy=default).parsebytes(raw)
    fields = {}
    files = []
    if message.is_multipart():
        for part in message.iter_parts():
            field_name = part.get_param('name', header='content-disposition')
            filename = part.get_filename()
            payload = part.get_payload(decode=True) or b''
            if filename:
                files.append({
                    'field': field_name or '',
                    'filename': filename,
                    'data': payload,
                })
            elif field_name:
                fields[field_name] = payload.decode(
                    part.get_content_charset() or 'utf-8', errors='replace'
                )
    return fields, files


def unique_path(folder, filename):
    safe_name = re.sub(r'[^A-Za-z0-9._-]+', '-', Path(filename).name).strip('-') or 'archivo'
    candidate = folder / safe_name
    counter = 2
    while candidate.exists():
        candidate = folder / f'{candidate.stem}-{counter}{candidate.suffix}'
        counter += 1
    return candidate


def parse_specs(raw_text):
    specs = {}
    for raw_line in raw_text.splitlines():
        line = raw_line.strip()
        if not line or ':' not in line:
            continue
        key, value = line.split(':', 1)
        key, value = key.strip(), value.strip()
        if key:
            specs[key] = value
    return specs


def specs_to_text(specs):
    return '\n'.join(f'{key}: {value}' for key, value in (specs or {}).items())


def save_uploaded_images(files):
    images = []
    for item in files:
        if item['field'] != 'images' or not item['data']:
            continue
        path = unique_path(UPLOADS, item['filename'])
        path.write_bytes(item['data'])
        images.append('assets/uploads/' + path.name)
    return images


def safe_delete_uploaded(relative_path):
    if not relative_path or not relative_path.startswith('assets/uploads/'):
        return
    candidate = (ROOT / relative_path).resolve()
    try:
        candidate.relative_to(UPLOADS.resolve())
    except ValueError:
        return
    if candidate.is_file():
        candidate.unlink(missing_ok=True)


def h(value):
    return html.escape(str(value or ''))


def new_form_token():
    return secrets.token_urlsafe(18)


def product_form(product=None):
    editing = bool(product)
    p = product or {}
    slug = p.get('slug', '')
    current_images = p.get('images') or []
    image_editor = ''
    if editing and current_images:
        cards = []
        for index, image_path in enumerate(current_images):
            checked = ' checked' if index == 0 else ''
            cards.append(f'''
              <div class="image-edit-card">
                <img src="/{h(image_path)}" alt="">
                <label class="inline"><input type="radio" name="cover_existing" value="{h(image_path)}"{checked}> Portada</label>
                <label class="inline remove"><input type="checkbox" name="remove_{index}" value="1"> Eliminar</label>
              </div>''')
        image_editor = f'''
          <label>Imágenes actuales</label>
          <div class="image-edit-grid">{''.join(cards)}</div>
          <small>Marca “Portada” para cambiar la imagen principal. Puedes eliminar imágenes individuales sin borrar el producto.</small>
        '''

    title = 'Editar producto' if editing else 'Agregar producto'
    action = '/admin/update-product' if editing else '/admin/add-product'
    required_images = '' if editing else ' required'
    button_text = 'Guardar cambios' if editing else 'Guardar producto'
    return f'''
      <section class="card product-form-card">
        <div class="card-head">
          <h2>{title}</h2>
          {f'<a class="text-link" href="/admin">Cancelar edición</a>' if editing else ''}
        </div>
        <form class="product-form" method="post" action="{action}" enctype="multipart/form-data" data-lock-submit>
          <input type="hidden" name="form_token" value="{new_form_token()}">
          {f'<input type="hidden" name="slug" value="{h(slug)}">' if editing else ''}
          <label>Nombre *</label>
          <input name="name" value="{h(p.get('name'))}" required>

          <label>Categoría *</label>
          <input name="category" value="{h(p.get('category'))}" placeholder="Repuestos, Accesorios, Llantas..." required>

          <div class="two-cols">
            <div><label>Precio (opcional)</label><input name="price" value="{h(p.get('price'))}" placeholder="Q 350.00"></div>
            <div><label>Código / referencia</label><input name="code" value="{h(p.get('code'))}"></div>
          </div>

          <label>Descripción corta</label>
          <textarea name="summary">{h(p.get('summary'))}</textarea>

          <label>Descripción completa</label>
          <textarea name="description">{h(p.get('description'))}</textarea>

          <label>Disponibilidad</label>
          <input name="availability" value="{h(p.get('availability') or 'Consultar')}">

          {image_editor}

          <label>{'Agregar más fotos' if editing else 'Fotos *'}</label>
          <input type="file" name="images" accept="image/*" multiple{required_images} data-image-input>
          <small>Selecciona todas las fotos del mismo producto en este único selector. Se guardarán dentro de una sola ficha.</small>
          <div class="selected-files" data-selected-files></div>

          <label>Especificaciones</label>
          <textarea name="specs" placeholder="Marca: NGK\nModelo: ABC\nCompatibilidad: ...">{h(specs_to_text(p.get('specs')))}</textarea>

          <button type="submit">{button_text}</button>
        </form>
      </section>
    '''


def product_rows(products):
    rows = []
    for p in products:
        first = (p.get('images') or [''])[0]
        rows.append(f'''
          <tr>
            <td><img src="/{h(first)}" alt=""></td>
            <td><b>{h(p.get('name'))}</b><small>{h(p.get('category'))} · {len(p.get('images') or [])} foto(s)</small></td>
            <td class="actions-cell">
              <a class="small-btn" href="/admin/edit-product?slug={urllib.parse.quote(p.get('slug',''))}">Editar</a>
              <form method="post" action="/admin/delete-product" enctype="multipart/form-data" onsubmit="return confirm('¿Eliminar este producto?');">
                <input type="hidden" name="slug" value="{h(p.get('slug'))}">
                <button class="danger small-btn" type="submit">Eliminar</button>
              </form>
            </td>
          </tr>
        ''')
    return ''.join(rows) or '<tr><td>No hay productos.</td></tr>'


def news_rows(news):
    rows = []
    for index, n in enumerate(news):
        media = n.get('media', n.get('image', ''))
        preview = (
            f'<video src="/{h(media)}" muted></video>'
            if n.get('type') == 'video'
            else f'<img src="/{h(media)}" alt="">'
        )
        rows.append(f'''
          <tr>
            <td>{preview}</td>
            <td><b>Elemento multimedia {index + 1}</b><small>{h(n.get('type','image').capitalize())}</small></td>
            <td class="actions-cell">
              <form method="post" action="/admin/delete-news" enctype="multipart/form-data" onsubmit="return confirm('¿Eliminar este elemento del carrusel?');">
                <input type="hidden" name="id" value="{h(n.get('id'))}">
                <button class="danger small-btn" type="submit">Eliminar</button>
              </form>
            </td>
          </tr>
        ''')
    return ''.join(rows) or '<tr><td>No hay contenido en el carrusel.</td></tr>'


def admin_html(message='', edit_product=None):
    products = load_json('products.json')
    news = load_json('news.json')
    return f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gestor Mayen</title>
<style>
*{{box-sizing:border-box}} body{{font-family:Arial,sans-serif;background:#f4f4f4;margin:0;color:#171717}} a{{color:inherit}}
header{{background:#111;color:#fff;padding:20px 4vw;display:flex;gap:18px;justify-content:space-between;align-items:center;position:sticky;top:0;z-index:5}}
header .header-links{{display:flex;gap:10px;flex-wrap:wrap}} header a{{color:#fff;text-decoration:none}}
main{{width:min(1180px,92%);margin:28px auto 60px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:24px}} .card{{background:#fff;padding:24px;border:1px solid #ddd;border-radius:8px}} .card-head{{display:flex;align-items:center;justify-content:space-between;gap:12px}}
h1,h2{{margin-top:0}} label{{display:block;font-weight:700;margin:13px 0 5px}} input,textarea{{width:100%;padding:11px;border:1px solid #bbb;border-radius:4px;font:inherit}} textarea{{min-height:90px;resize:vertical}} button,.btn{{background:#ef2e38;color:#fff;border:0;padding:11px 16px;font-weight:700;cursor:pointer;text-decoration:none;display:inline-block;margin-top:12px;border-radius:4px}} .btn-dark{{background:#222}} .danger{{background:#222;margin:0}} .small-btn{{padding:8px 11px;margin:0;font-size:13px}}
table{{width:100%;border-collapse:collapse}} td{{border-top:1px solid #eee;padding:9px;vertical-align:middle}} td img,td video{{width:80px;height:58px;object-fit:cover;background:#111;border-radius:4px}} small{{display:block;color:#777;margin-top:4px;line-height:1.35}} .msg{{background:#e8f6eb;border:1px solid #b9ddc0;padding:12px;margin-bottom:20px;border-radius:6px}} .hint{{background:#fff4e4;border:1px solid #ead2a7;padding:14px;font-size:14px;margin-bottom:24px;border-radius:6px}} .actions-cell{{display:flex;gap:7px;justify-content:flex-end;align-items:center}} .actions-cell form{{margin:0}} .text-link{{font-size:14px;color:#b11;text-decoration:none;font-weight:700}}
.two-cols{{display:grid;grid-template-columns:1fr 1fr;gap:12px}} .image-edit-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(135px,1fr));gap:10px;margin-top:8px}} .image-edit-card{{border:1px solid #ddd;padding:8px;border-radius:6px}} .image-edit-card img{{width:100%;aspect-ratio:1/1;object-fit:cover;background:#eee;border-radius:4px}} label.inline{{display:flex;gap:7px;align-items:center;margin:8px 0 0;font-weight:500;font-size:13px}} label.inline input{{width:auto}} label.inline.remove{{color:#9d2020}} .selected-files{{font-size:13px;color:#555;margin-top:7px}} .selected-files span{{display:block}}
@media(max-width:850px){{.grid{{grid-template-columns:1fr}} .two-cols{{grid-template-columns:1fr}} header{{align-items:flex-start;flex-direction:column}}}}
</style>
</head>
<body>
<header>
  <b>Gestor local · Mayen V Petapa</b>
  <div class="header-links">
    <a href="/index.html" target="_blank">Ver sitio ↗</a>
    <a href="/admin/export" class="btn btn-dark" style="margin:0">Descargar paquete para publicar</a>
  </div>
</header>
<main>
  {f'<div class="msg">{h(message)}</div>' if message else ''}
  <div class="hint"><b>Seguridad:</b> este gestor escucha únicamente en <code>127.0.0.1</code> (tu propia computadora). El botón “Descargar paquete para publicar” genera un ZIP sin el gestor, sin Python y sin archivos administrativos.</div>

  <div class="grid">
    {product_form(edit_product)}
    <section class="card">
      <h2>Agregar al carrusel</h2>
      <p>Sube directamente el arte terminado. Puede ser una <b>imagen</b> o un <b>video</b>; no necesitas escribir título ni descripción.</p>
      <form method="post" action="/admin/add-news" enctype="multipart/form-data" data-lock-submit>
        <input type="hidden" name="form_token" value="{new_form_token()}">
        <label>Imagen o video *</label>
        <input type="file" name="media" accept="image/*,video/mp4,video/webm,video/quicktime,.m4v" required>
        <small>Imágenes: JPG, PNG, WebP. Videos recomendados: MP4 o WebM.</small>
        <button type="submit">Agregar al carrusel</button>
      </form>
    </section>
  </div>

  <div class="grid" style="margin-top:24px">
    <section class="card"><h2>Productos ({len(products)})</h2><table>{product_rows(products)}</table></section>
    <section class="card"><h2>Carrusel ({len(news)})</h2><table>{news_rows(news)}</table></section>
  </div>
</main>
<script>
document.querySelectorAll('[data-image-input]').forEach(input => {{
  input.addEventListener('change', () => {{
    const box = input.closest('form').querySelector('[data-selected-files]');
    if (!box) return;
    const files = [...input.files];
    box.innerHTML = files.length ? '<b>Archivos seleccionados:</b>' + files.map((f,i)=>`<span>${{i+1}}. ${{f.name}}</span>`).join('') : '';
  }});
}});
document.querySelectorAll('[data-lock-submit]').forEach(form => {{
  form.addEventListener('submit', () => {{
    const button = form.querySelector('button[type="submit"]');
    if (button) {{ button.disabled = true; button.textContent = 'Guardando…'; }}
  }});
}});
</script>
</body></html>'''


def token_already_used(fields):
    token = fields.get('form_token', '')
    if not token:
        return False
    if token in USED_FORM_TOKENS:
        return True
    USED_FORM_TOKENS.add(token)
    return False


def public_zip_bytes():
    save_public_data()
    buffer = io.BytesIO()
    include_top = [
        '.htaccess', '404.html', 'index.html', 'nosotros.html',
        'producto.html', 'repuestos.html', 'taller.html'
    ]
    include_dirs = ['assets', 'css', 'js']
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name in include_top:
            path = ROOT / name
            if path.is_file():
                zf.write(path, path.relative_to(ROOT).as_posix())
        for dirname in include_dirs:
            base = ROOT / dirname
            if not base.exists():
                continue
            for path in base.rglob('*'):
                if path.is_file():
                    zf.write(path, path.relative_to(ROOT).as_posix())
    return buffer.getvalue()


class Handler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        path = urllib.parse.urlparse(path).path
        relative = Path(urllib.parse.unquote(path.lstrip('/')))
        return str(ROOT / relative)

    def send_html(self, content, status=200):
        body = content.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def redirect(self, message='Guardado'):
        self.send_response(303)
        self.send_header('Location', '/admin?msg=' + urllib.parse.quote(message))
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)

        if parsed.path == '/admin':
            self.send_html(admin_html(query.get('msg', [''])[0]))
            return

        if parsed.path == '/admin/edit-product':
            slug = query.get('slug', [''])[0]
            product = next((p for p in load_json('products.json') if p.get('slug') == slug), None)
            if not product:
                self.send_html(admin_html('Producto no encontrado.'), 404)
            else:
                self.send_html(admin_html('', product))
            return

        if parsed.path == '/admin/export':
            payload = public_zip_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="MAYEN_PUBLICAR.zip"')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        fields, files = parse_multipart(self)

        if parsed.path in ('/admin/add-product', '/admin/update-product', '/admin/add-news') and token_already_used(fields):
            self.redirect('La operación ya había sido procesada. No se creó un duplicado.')
            return

        if parsed.path == '/admin/add-product':
            name = fields.get('name', '').strip()
            images = save_uploaded_images(files)
            if not name or not images:
                self.redirect('El producto necesita nombre y al menos una imagen.')
                return

            products = load_json('products.json')
            slug = slugify(name)
            base = slug
            counter = 2
            while any(item.get('slug') == slug for item in products):
                slug = f'{base}-{counter}'
                counter += 1

            product = {
                'slug': slug,
                'name': name,
                'category': fields.get('category', '').strip(),
                'price': fields.get('price', '').strip(),
                'code': fields.get('code', '').strip(),
                'summary': fields.get('summary', '').strip(),
                'description': fields.get('description', '').strip(),
                'availability': fields.get('availability', 'Consultar').strip() or 'Consultar',
                'images': images,
                'specs': parse_specs(fields.get('specs', '')),
            }
            # Una sola inserción por envío, independientemente de cuántas imágenes haya.
            products.append(product)
            write_json('products.json', products)
            save_public_data()
            self.redirect(f'Producto agregado con {len(images)} foto(s) en una sola ficha.')
            return

        if parsed.path == '/admin/update-product':
            slug = fields.get('slug', '').strip()
            products = load_json('products.json')
            index = next((i for i, p in enumerate(products) if p.get('slug') == slug), None)
            if index is None:
                self.redirect('No se encontró el producto a editar.')
                return

            old = products[index]
            current_images = list(old.get('images') or [])
            remaining = []
            for idx, image_path in enumerate(current_images):
                if fields.get(f'remove_{idx}') == '1':
                    safe_delete_uploaded(image_path)
                else:
                    remaining.append(image_path)

            new_images = save_uploaded_images(files)
            images = remaining + new_images
            cover = fields.get('cover_existing', '')
            if cover in images:
                images.remove(cover)
                images.insert(0, cover)

            if not images:
                self.redirect('No se guardaron los cambios porque el producto debe conservar al menos una imagen.')
                return

            updated = {
                **old,
                'name': fields.get('name', old.get('name', '')).strip(),
                'category': fields.get('category', old.get('category', '')).strip(),
                'price': fields.get('price', '').strip(),
                'code': fields.get('code', '').strip(),
                'summary': fields.get('summary', '').strip(),
                'description': fields.get('description', '').strip(),
                'availability': fields.get('availability', 'Consultar').strip() or 'Consultar',
                'images': images,
                'specs': parse_specs(fields.get('specs', '')),
            }
            products[index] = updated
            write_json('products.json', products)
            save_public_data()
            self.redirect('Producto actualizado correctamente.')
            return

        if parsed.path == '/admin/add-news':
            media = ''
            media_type = 'image'
            for item in files:
                if item['field'] == 'media' and item['data']:
                    path = unique_path(NEWS, item['filename'])
                    path.write_bytes(item['data'])
                    media = 'assets/news/' + path.name
                    mime = mimetypes.guess_type(item['filename'])[0] or ''
                    media_type = 'video' if mime.startswith('video/') or path.suffix.lower() in ('.mp4', '.webm', '.mov', '.m4v') else 'image'
                    break
            if not media:
                self.redirect('Selecciona una imagen o video.')
                return
            news = load_json('news.json')
            next_id = str(max([int(x.get('id', 0)) for x in news] + [0]) + 1)
            news.append({'id': next_id, 'type': media_type, 'media': media})
            write_json('news.json', news)
            save_public_data()
            self.redirect('Contenido multimedia agregado al carrusel.')
            return

        if parsed.path == '/admin/delete-product':
            slug = fields.get('slug', '')
            products = load_json('products.json')
            target = next((p for p in products if p.get('slug') == slug), None)
            if target:
                for image_path in target.get('images') or []:
                    safe_delete_uploaded(image_path)
            products = [p for p in products if p.get('slug') != slug]
            write_json('products.json', products)
            save_public_data()
            self.redirect('Producto eliminado.')
            return

        if parsed.path == '/admin/delete-news':
            news_id = fields.get('id', '')
            news = load_json('news.json')
            kept = []
            for item in news:
                if str(item.get('id')) == news_id:
                    media = item.get('media', '')
                    if media.startswith('assets/news/'):
                        path = (ROOT / media).resolve()
                        try:
                            path.relative_to(NEWS.resolve())
                            path.unlink(missing_ok=True)
                        except ValueError:
                            pass
                else:
                    kept.append(item)
            write_json('news.json', kept)
            save_public_data()
            self.redirect('Elemento eliminado del carrusel.')
            return

        self.send_error(404)


if __name__ == '__main__':
    save_public_data()
    url = 'http://localhost:8000/admin'
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    print('Gestor Mayen abierto en', url)
    print('Solo escucha en 127.0.0.1 (esta computadora).')
    print('Para detener: Ctrl+C')
    ThreadingHTTPServer(('127.0.0.1', 8000), Handler).serve_forever()
