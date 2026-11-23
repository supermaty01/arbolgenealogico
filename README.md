<img src="assets/icon.svg" width="64" height="64" alt="">

# Genealogía Álvarez del Pino

Árbol genealógico de **Manuel Salvador Álvarez del Pino Ruiz**, a partir de la investigación familiar original (14 documentos de Word: textos, fotos y 28 cuadros de ascendientes).

Hay dos formatos:

| Formato | Dónde | Qué tiene |
|---|---|---|
| **Página web** | `docs/` (GitHub Pages) | Árbol interactivo en abanico o en árbol, con zoom, buscador, ficha de cada persona, historia de la familia, índice y los 28 cuadros originales ampliables. Funciona en celular. |
| **Libro** | `libro/Genealogia-Alvarez-del-Pino.pdf` | 70 páginas A4 verticales, listo para imprimir (márgenes en espejo, capítulos en página impar): portada, metodología, origen del apellido, el linaje Álvarez del Pino, la familia de Manuel Salvador, el árbol en abanico, 62 láminas verticales del árbol completo e índice de personas con su lámina. |

## Publicar la web en GitHub Pages

1. En GitHub: **Settings → Pages**.
2. *Source*: **Deploy from a branch** → rama `master`, carpeta **`/docs`** → *Save*.
3. En uno o dos minutos queda en `https://<usuario>.github.io/arbolgenealogico/`.

> GitHub Pages solo es gratis en repositorios **públicos** (en privados requiere GitHub Pro).

Para verla en tu computador: `cd docs && python -m http.server` y abrir <http://localhost:8000>. Si abres `index.html` con doble clic no carga los datos, porque el navegador bloquea la lectura del JSON.

## Cómo se construyó (y cómo regenerarlo)

Los cuadros originales están hechos con espacios y colores en Word, no con tablas. Para extraerlos:

1. **Word → PDF** con Word, para conservar la posición exacta de cada palabra.
2. **`scripts/tree.py`**: lee las palabras con sus coordenadas (PyMuPDF) y reconstruye cada cuadro por franjas de generación. Usa la «Y» que une a cada pareja y las marcas `|` y `XXX` para saber quién es hijo de quién. Salida: `datos/arboles-parseados.json`.
3. **`scripts/build_data.py`**: limpia los nombres y los lugares (ESP → España, MED → Medellín…). Enlaza las hojas del cuadro 1 con los cuadros donde continúan y une a la misma persona cuando aparece en varios cuadros. Por ejemplo, Juan Vélez de Rivero aparece en más de diez. Salida: `datos/personas.json` (520 personas únicas a partir de 2.139 apariciones).
4. **`scripts/build_site.py`**: añade la narrativa (`contenido/historia.json`), las fotos, los hijos y hermanos de Manuel Salvador y las imágenes de los cuadros, y genera `docs/data/familia.json`.
5. **`scripts/build_book.py . --pdf`**: genera `libro/libro.html` y lo imprime a PDF con Edge (Playwright). `scripts/laminas.py` reparte el árbol en láminas verticales: cada una tiene como máximo 7 columnas y 10 generaciones, y lo que no cabe continúa en otra lámina. El script añade páginas en blanco para que cada capítulo empiece en página impar.

```bash
pip install pymupdf pillow playwright
python -P scripts/tree.py cuadros.pdf "12:1,13:2,...,39:28" datos/arboles-parseados.json
python scripts/build_data.py datos/arboles-parseados.json datos/personas.json
python -P scripts/build_site.py datos/personas.json contenido/historia.json cuadros.pdf <carpeta_fotos> docs
python scripts/build_book.py . --pdf
```

`scripts/overlay.py` dibuja sobre cada cuadro las cajas y los enlaces detectados. Sirve para revisar la extracción a ojo.

### Limitaciones conocidas

- La extracción es automática. En las generaciones más antiguas (1500–1600), algunos cuadros tienen una disposición irregular: un padre o una madre sin pareja, o texto partido en dos líneas. Unas pocas personas de esa zona pueden quedar mal enlazadas o con el nombre incompleto. Por eso los cuadros originales se incluyen completos en la web y en el libro.
- Como advierte la propia investigación, las fechas no siempre indican si son de nacimiento o de muerte.
- Para corregir un texto de la historia, edita `contenido/historia.json` y vuelve a correr los pasos 4 y 5.
