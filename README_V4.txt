MAYEN WEB V4

CAMBIOS DEL GESTOR
- Corregido el alta de productos con varias imágenes: un envío crea UNA sola ficha con todas las fotos seleccionadas.
- Protección adicional contra doble envío accidental del mismo formulario.
- Botón EDITAR para cada producto existente.
- Al editar puedes cambiar nombre, categoría, precio, código, descripciones, disponibilidad y especificaciones.
- Al editar puedes agregar más imágenes, eliminar imágenes individuales y cambiar la portada.
- El slug/URL interna del producto se conserva al editar para no romper enlaces ya compartidos.
- Al borrar productos se eliminan también las imágenes subidas por el gestor que ya no se necesitan.

PUBLICACIÓN SEGURA
- El gestor corre únicamente en 127.0.0.1:8000. Eso significa que solo está disponible desde la misma computadora donde ejecutas gestor.py.
- NO hace falta publicar gestor.py ni los archivos .bat en Bluehost.
- En el gestor existe el botón "Descargar paquete para publicar".
- Ese botón crea/descarga MAYEN_PUBLICAR.zip con SOLO los archivos públicos de la web: HTML, CSS, JS e imágenes/videos.
- El ZIP público no contiene gestor.py, data/, archivos .bat, README ni __pycache__.

FLUJO RECOMENDADO
1. Ejecuta gestor.py localmente.
2. Agrega/edita/elimina productos y contenido del carrusel.
3. Revisa la web localmente.
4. Pulsa "Descargar paquete para publicar".
5. Sube el contenido de MAYEN_PUBLICAR.zip al public_html de Bluehost y sobrescribe los archivos anteriores.

QUÉ CAMBIA CUANDO EDITAS UN PRODUCTO
- data/products.json: base editable local.
- js/products.js: copia pública que usa la web.
- assets/uploads/: fotografías subidas por el gestor.

QUÉ CAMBIA CUANDO EDITAS EL CARRUSEL
- data/news.json: base editable local.
- js/news.js: copia pública que usa la web.
- assets/news/: imágenes/videos del carrusel.

GITHUB
- Puedes subir el proyecto completo a un repositorio PRIVADO para tener respaldo/versionado.
- Si el repositorio es público, recuerda que todo su contenido será visible. No guardes contraseñas, claves API, tokens ni credenciales en el proyecto.
- El número de WhatsApp y las imágenes de productos ya son información pública del sitio, por lo que no son secretos.
- Para publicar en Bluehost no necesitas clonar el repositorio: el método más sencillo sigue siendo exportar MAYEN_PUBLICAR.zip desde el gestor.

CONTRASEÑA DEL GESTOR
- Para este gestor LOCAL no es necesaria una contraseña porque el servidor está enlazado exclusivamente a 127.0.0.1.
- Aunque otra persona conozca http://tudominio.com/admin, esa ruta NO existe en el paquete público.
- Si en el futuro quieres administrar productos directamente desde Internet, entonces sí habrá que construir un backend con autenticación real, HTTPS y credenciales almacenadas de forma segura. No se debe proteger un panel web solo con una contraseña escrita en JavaScript.
