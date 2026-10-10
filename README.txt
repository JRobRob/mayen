MAYEN WEB v2
============

FORMA MÁS FÁCIL DE ADMINISTRAR PRODUCTOS Y NOTICIAS
---------------------------------------------------
1. Extrae toda la carpeta del ZIP.
2. Haz doble clic en ABRIR_GESTOR.bat.
3. Se abrirá http://localhost:8000/admin en el navegador.
4. Desde ahí puedes:
   - agregar productos,
   - subir varias fotos de un producto,
   - eliminar productos,
   - agregar noticias con imagen al carrusel de Inicio,
   - eliminar noticias.
5. El gestor copia las imágenes y actualiza el catálogo automáticamente.
6. Para revisar la web, usa el enlace "Ver sitio" dentro del gestor.
7. Para cerrar el gestor, vuelve a la ventana negra y presiona Ctrl+C.

IMPORTANTE
---------
El gestor es LOCAL: sirve para preparar la web desde tu computadora sin editar código.
Cuando termines los cambios, sube la carpeta completa a Bluehost. El sitio publicado es estático y no necesita Python.

Si Windows no abre el BAT:
- abre la carpeta,
- escribe cmd en la barra de dirección,
- presiona Enter,
- ejecuta: py gestor.py
Si "py" no funciona, ejecuta: python gestor.py

PRODUCTOS
---------
Ya no hay que crear un HTML por producto.
Todos se guardan en data/products.json y el gestor genera js/products.js.
La ficha universal es producto.html?p=nombre-del-producto.
Las imágenes se guardan automáticamente en assets/uploads/.

NOTICIAS
--------
Se guardan en data/news.json y las imágenes en assets/news/.
El carrusel aparece automáticamente en Inicio cuando existe al menos una noticia.
Si no hay noticias, la sección no aparece.

WHATSAPP
--------
El número se configura en js/config.js.
Actualmente usa el número temporal +502 5100-1616.

BLUEHOST
--------
Sube el contenido de esta carpeta a public_html. index.html debe quedar directamente dentro de public_html.
NO es necesario subir gestor.py ni los .bat para que la web funcione, aunque no pasa nada si quedan en la carpeta.
