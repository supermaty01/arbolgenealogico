<img src="assets/icon.svg" width="64" height="64" alt="">

# Genealogía Álvarez Ruiz

Árbol genealógico de los hijos de **Manuel Salvador Álvarez Ruiz** y **María Teresa Ruiz Maya**, a partir de dos investigaciones familiares originales:

- la de Manuel Salvador: 14 documentos de Word con textos, fotos y 28 cuadros de ascendientes;
- la de María Teresa: dos documentos de Word con sus cuadros n.º 1 a 11 y 16 a 19 y sus continuaciones (3A, 3B…, 17A…17G), que llegan hasta los linajes medievales de España;
- documentos complementarios: el árbol de la línea directa del apellido (con los años de vida de cada generación), el texto «Genealogía Álvarez del Pino» (fechas de matrimonios y testamentos, ramas colaterales) y dos cuadros sueltos, de Fermín Álvarez Velásquez y de Fernando Antonio Arango Vélez.

Manuel Salvador y María Teresa eran parientes: la madre de él (Trinidad Ruiz Velásquez) y la abuela materna de ella (Dolores Ruiz Velásquez) eran hermanas. Por eso más de 500 antepasados aparecen en las dos ramas.

Hay dos formatos:

| Formato | Dónde | Qué tiene |
|---|---|---|
| **Página web** | `docs/` (GitHub Pages) | Árbol interactivo en abanico o en árbol, que parte de los hijos, con zoom, buscador y ficha de cada persona (incluye si es antepasado de ambos). También tiene la historia de la familia, el índice con filtros por lado y por línea, y los cuadros originales ampliables (65 cuadros, más 7 páginas medievales solo como imagen). Funciona en celular. |
| **Libro** | `libro/Genealogia-Alvarez-Ruiz.pdf` | Páginas A4 verticales, listo para imprimir (márgenes en espejo, capítulos en página impar). Incluye portada, metodología, origen del apellido, el linaje Álvarez del Pino, la familia de Manuel Salvador y María Teresa, el árbol en abanico, las láminas verticales del árbol completo y el índice de personas con su lámina. |

## Publicar la web en GitHub Pages

1. En GitHub: **Settings → Pages**.
2. *Source*: **Deploy from a branch** → rama `master`, carpeta **`/docs`** → *Save*.
3. En uno o dos minutos queda en `https://<usuario>.github.io/arbolgenealogico/`.

> GitHub Pages solo es gratis en repositorios **públicos** (en privados requiere GitHub Pro).

Para verla en tu computador: `cd docs && python -m http.server` y abrir <http://localhost:8000>. Si abres `index.html` con doble clic no carga los datos, porque el navegador bloquea la lectura del JSON.

Para medir el rendimiento (carga, número de nodos y tiempo por fotograma al hacer zoom y arrastrar, en escritorio y en celular con la CPU limitada 4x): `python -P scripts/perf.py --check`. Necesita Playwright y Edge; `--docs` mide otra copia de la web, `--out` guarda las cifras en JSON y `--shots` guarda capturas para comparar el aspecto.

## Cómo se construyó (y cómo regenerarlo)

Los cuadros originales están hechos con espacios y colores en Word, no con tablas. Para extraerlos:

1. **Word → PDF** con Word, para conservar la posición exacta de cada palabra. Para María Teresa se unen en un solo PDF los dos documentos: `# 1 - MARIA TERESA RUIZ MAYA` (págs. 1-55) y `MARIA TERESA RUIZ MAYA PARTE 2` (págs. 56-79).
2. **`scripts/tree.py`**: lee las palabras con sus coordenadas (PyMuPDF) y reconstruye cada cuadro por franjas de generación. Usa la «Y» que une a cada pareja y las marcas `|` y `XXX` para saber quién es hijo de quién. Los cuadros de Manuel Salvador tienen sus páginas fijas en el script. Los de María Teresa se describen en `datos/teresa-cuadros.json`, con las páginas y franjas de cada cuadro. Los cuadros sueltos se describen igual en `datos/complementos-cuadros.json` (claves 201+). Salida: `datos/arboles-parseados.json`, `datos/teresa-parseados.json` y `datos/complementos-parseados.json`.
3. **`scripts/build_data.py`**: limpia los nombres y los lugares (ESP → España, MED → Medellín…). Enlaza los cuadros entre sí y une a la misma persona cuando aparece en varios cuadros, también entre las dos ramas. El cuadro n.º 1 de María Teresa pone la última generación en un bloque aparte, numerado por persona, y se enlaza a mano en `fix_teresa1`. Los cuadros complementarios solo completan: el nombre, la fecha y los padres de cada persona salen de los cuadros principales cuando estos los traen. Salida: `datos/personas.json`.
4. **`scripts/build_site.py`**: añade la raíz (los hijos), las seis líneas, la narrativa (`contenido/historia.json`, con los años de vida del árbol de línea directa en la clave `vida`), las fotos, los hijos y hermanos de Manuel Salvador y las imágenes de los cuadros. Genera `docs/data/familia.json`. Con `SKIP_IMG=1` no vuelve a dibujar las imágenes de los cuadros.
5. **`scripts/build_book.py . --pdf`**: genera `libro/libro.html` y lo imprime a PDF con Edge (Playwright). `scripts/laminas.py` reparte el árbol en láminas verticales: cada una tiene como máximo 7 columnas y 10 generaciones, y lo que no cabe continúa en otra lámina. El script añade páginas en blanco para que cada capítulo empiece en página impar.

```bash
pip install pymupdf pillow playwright
python -P scripts/tree.py cuadros.pdf "12:1,13:2,...,39:28" datos/arboles-parseados.json
python -P scripts/tree.py teresa.pdf datos/teresa-cuadros.json datos/teresa-parseados.json
python -P scripts/tree.py complementos.pdf datos/complementos-cuadros.json datos/complementos-parseados.json
python scripts/build_data.py datos/arboles-parseados.json datos/personas.json datos/teresa-parseados.json datos/complementos-parseados.json
python -P scripts/build_site.py datos/personas.json contenido/historia.json cuadros.pdf <carpeta_fotos> docs teresa.pdf datos/teresa-cuadros.json complementos.pdf datos/complementos-cuadros.json
python scripts/build_book.py . --pdf
```

`scripts/overlay.py` dibuja sobre cada cuadro las cajas y los enlaces detectados. Sirve para revisar la extracción a ojo.

### Limitaciones conocidas

- La extracción es automática. En las generaciones más antiguas, algunos cuadros tienen una disposición irregular: un padre o una madre sin pareja, o texto partido en dos líneas. Unas pocas personas de esa zona pueden quedar mal enlazadas o con el nombre incompleto. Por eso los cuadros originales se incluyen completos en la web.
- Las páginas medievales de María Teresa (17A a 17G: Ponce de León, Guzmán, reyes de León, Castilla, Navarra y Asturias, visigodos) son las más densas e irregulares. Sus ramas que no se pudieron enlazar con el resto del árbol se dejaron fuera del árbol y del libro. Las páginas que son copias reducidas o repetidas, o cuyo diseño no se pudo leer, no se extrajeron. Todas siguen disponibles como imagen en la sección de cuadros originales de la web.
- Como advierte la propia investigación, las fechas no siempre indican si son de nacimiento o de muerte.
- Para corregir un texto de la historia, edita `contenido/historia.json` y vuelve a correr los pasos 4 y 5.
