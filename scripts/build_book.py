"""Genera el libro (libro/libro.html) a partir de docs/data/familia.json y lo imprime a PDF.

Uso: python build_book.py <carpeta_repo> [--pdf]
"""
import sys, os, json, html, collections
sys.stdout.reconfigure(encoding='utf-8')
REPO = os.path.abspath(sys.argv[1])
D = json.load(open(os.path.join(REPO, 'docs/data/familia.json'), encoding='utf-8'))
H = D['historia']; P = {p['id']: p for p in D['people']}; ROOT = D['root']; LINES = D['lines']
MANUEL, TERESA = D['manuel'], D['teresa']
LCOL = ['#1f6f78', '#a23b48', '#b07a12', '#4d5fa3', '#3f7d3a', '#8a4f9e']; INK = '#2a2622'
e = lambda s: html.escape(str(s or ''))
col = lambda p: LCOL[p['line']] if p.get('line', -1) >= 0 else INK

ORD = ['', '', '', '', 'cuarto', 'quinto', 'sexto', 'séptimo', 'octavo', 'noveno', 'décimo', 'undécimo',
       'duodécimo', 'decimotercer', 'decimocuarto', 'decimoquinto', 'decimosexto', 'decimoséptimo']
def gen_title(g):
    if g == 0: return 'Hijos'
    return {1: 'Padres', 2: 'Abuelos', 3: 'Bisabuelos', 4: 'Tatarabuelos'}.get(g) or (ORD[g - 1].capitalize() + 's abuelos' if g - 1 < len(ORD) else f'{g - 1}.º abuelos')
def meta(p): return ' · '.join(x for x in [p.get('year'), p.get('place')] if x)

anc = [p for p in D['people'] if p.get('gen') and p['gen'] > 1 and not p.get('sibling')]
both = sum(1 for p in anc if p.get('both'))
nT = sum(1 for t in D['trees'] if t['side'] == 'T' and not t.get('name'))
def kin():
    b = sorted((p for p in anc if p.get('both')), key=lambda p: p['genM'] + p['genT'])[0]
    sp = next((P[x] for x in b.get('spouses', []) if x in P and P[x].get('both')), None)
    word = lambda g: gen_title(g + 0).lower()
    return b, sp, word(b['genM']), word(b['genT'])
KB, KS, KWM, KWT = kin()
KIN = (f'Manuel Salvador y María Teresa eran parientes: {e(KB["name"])}{" y " + e(KS["name"]) if KS else ""} eran {KWM} '
       f'de él y {KWT} de ella. Por eso {both} de los {len(anc)} antepasados aparecen en las dos ramas del árbol.')
max_gen = max(p['gen'] for p in anc)
min_year = min(int(p['year'][:4]) for p in anc if p.get('year'))
by_gen = collections.Counter(p['gen'] for p in anc)

out = []
w = out.append

# ---------------- portada
w(f'''<section class="cover">
  <div class="cover-art"><svg id="fan" viewBox="-1000 -1000 2000 2000"></svg></div>
  <div class="cover-text">
    <div class="kicker">Genealogía de los hijos de</div>
    <h1>Manuel Salvador Álvarez Ruiz<br><span class="amp">y</span> María Teresa Ruiz Maya</h1>
    <p class="sub">{e(H['subtitulo'])}</p>
    <p class="meta">{len(anc)} antepasados · {max_gen - 1} generaciones</p>
  </div>
</section>''')

# ---------------- presentación y contenido
w('<!--SP:0-->')
w(f'''<section class="front">
  <h2 class="small-title">Presentación</h2>
  <p class="big">Este libro reúne la investigación genealógica de la familia de Manuel Salvador Álvarez Ruiz, arriero de San Cristóbal asentado en San Antonio de Prado, y de su esposa María Teresa Ruiz Maya: la historia del apellido Álvarez del Pino, el linaje que llegó a Antioquia a comienzos del siglo XVII y la ascendencia de los dos, que es la de sus once hijos.</p>
  <p>La información proviene de dos investigaciones: los 28 cuadros de ascendientes de Manuel Salvador, con los textos de su linaje, y los {nT} cuadros de María Teresa, que llegan hasta los linajes medievales de España. Como muchos antepasados aparecen varias veces —algo habitual en las familias antioqueñas de la Colonia, donde los matrimonios entre parientes eran frecuentes—, en este libro cada persona se cuenta una sola vez: en total, <b>{len(anc)} antepasados distintos</b>.</p>
  <p>Después se sumaron documentos complementarios: un árbol de la línea directa del apellido, desde Diego Álvarez Loaiza (1534–1590), con los años de vida de cada generación; el texto «Genealogía Álvarez del Pino», con fechas de matrimonios y testamentos y otras ramas de la familia; y dos cuadros sueltos, de Fermín Álvarez Velásquez y de Fernando Antonio Arango Vélez. Esos cuadros solo completan lo que faltaba: donde dicen algo distinto de los cuadros principales, se conservan los principales.</p>
  <p>{KIN}</p>
  <p>Los nombres, lugares y fechas se transcribieron tal como aparecen en los cuadros originales; el árbol se redibujó en láminas para leerlo de arriba hacia abajo, generación por generación. Cuando un dato aparece escrito de varias maneras, se conservó la forma más completa. Los cuadros originales pueden consultarse en la versión digital.</p>
  <h2 class="small-title" style="margin-top:14mm">Contenido</h2>
  <ol class="toc">
    <li><span>Metodología y notas del autor</span></li>
    <li><span>Álvarez: origen y significado</span></li>
    <li><span>El linaje Álvarez del Pino</span></li>
    <li><span>Manuel Salvador, María Teresa y sus hijos</span></li>
    <li><span>El árbol de ascendientes</span></li>
    <li><span>Láminas del árbol</span></li>
    <li><span>Índice de personas</span></li>
  </ol>
</section>''')

# ---------------- 1. metodología
m = H['metodologia']
w('<!--SP:1-->')
w(f'''<section class="chapter"><div class="chap-n">Capítulo 1</div><h1>Metodología y notas del autor</h1>
<p class="lead">La metodología del trabajo fue:</p><ol class="num">{''.join(f'<li>{e(i)}</li>' for i in m['items'])}</ol>
<h3>Notas para leer los cuadros</h3><ul class="notes">{''.join(f'<li>{e(i)}</li>' for i in m['notas'])}</ul>
<div class="aside"><b>Cómo leer las fechas.</b> En los cuadros, cada persona lleva debajo un lugar y un año abreviados: <i>ESP.</i> España, <i>MED.</i> Medellín, <i>ANT.</i> Antioquia, <i>SANTA FE</i> Santa Fe de Antioquia, <i>BOG.</i> Bogotá, <i>REM.</i> Remedios, <i>ZARAG.</i> Zaragoza. «X» indica un dato desconocido y «XXX», que no se conoce la ascendencia de esa persona.</div>
</section>''')

# ---------------- 2. origen
o = H['origen']
w('<!--SP:2-->')
w(f'''<section class="chapter"><div class="chap-n">Capítulo 2</div><h1>{e(o['titulo'])}</h1>
{''.join(f'<p class="{"lead drop" if i == 0 else ""}">{e(t)}</p>' for i, t in enumerate(o['parrafos']))}
</section>''')

# ---------------- 3. linaje
w('<!--SP:3-->')
w('''<section class="chapter"><div class="chap-n">Capítulo 3</div><h1>El linaje Álvarez del Pino</h1>
<p class="lead">Diez generaciones por línea de varón, desde don Diego Álvarez del Pino, fundador de la familia en Antioquia, hasta Manuel Salvador Álvarez Ruiz. Los cuadros conservan además los nombres de tres generaciones anteriores en España.</p>''')
# diagrama de la línea
line_ids = []
x = MANUEL
while x:
    line_ids.append(x); x = P[x].get('father')
line_ids.reverse()
w('<div class="lineage">')
first = next(i for i, pid in enumerate(line_ids) if P[pid].get('bio') == 1)
for i, pid in enumerate(line_ids):
    p = P[pid]
    num = str(i - first + 1) if i >= first else '·'
    sp = ', '.join(P[s]['name'] for s in p.get('spouses', []) if s in P)
    w(f'''<div class="lin-row{' hl' if p.get('bio') else ''}"><span class="lin-g">{num}</span><div><b>{e(p['name'])}</b>{f' <span class="yr">{e(meta(p))}</span>' if meta(p) else ''}{f'<br><span class="sp">casado con {e(sp)}</span>' if sp else ''}</div></div>''')
w('</div>')
for g in H['linaje']:
    w(f'''<article class="gen"><div class="gen-head"><span class="gen-n">{g['n']}</span><div><h2>{e(g['titulo'])}</h2>
    <div class="dates">{e(g['fechas'])}</div><div class="subt">{e(g['subtitulo'])}</div></div></div>''')
    for t in g['parrafos']: w(f'<p>{e(t)}</p>')
    if g.get('fotos'):
        w('<div class="photos">' + ''.join(f'<figure><img src="../docs/img/{f}"><figcaption>{e(H["fotos"][f])}</figcaption></figure>' for f in g['fotos']) + '</div>')
    if g.get('testimonio'):
        t = g['testimonio']
        w(f'<blockquote><p>«{e(t["texto"])}»</p><cite>{e(t["titulo"])} — {e(t["autor"])}</cite></blockquote>')
    if g.get('hijos'):
        w(f'<p class="kids-t">{e(g["hijos_titulo"])}</p><ol class="kids">' + ''.join(f'<li>{e(k)}</li>' for k in g['hijos']) + '</ol>')
    if g.get('hijos2'):
        w(f'<p class="kids-t">{e(g["hijos2_titulo"])}</p><ol class="kids">' + ''.join(f'<li>{e(k)}</li>' for k in g['hijos2']) + '</ol>')
    if g['n'] == 10:
        w(f'<p class="kids-t">{e(g["hijos_titulo"])}</p>')
    w('</article>')
w('</section>')

# ---------------- 4. familia de Manuel Salvador
kids = sorted([p for p in D['people'] if p.get('child')], key=lambda p: p['year'])
def nm(pid): return e(P[pid]['name']) if pid and pid in P else '—'
T = P[TERESA]; TF, TM = T.get('father'), T.get('mother')
w('<!--SP:4-->')
w(f'''<section class="chapter"><div class="chap-n">Capítulo 4</div><h1>Manuel Salvador, María Teresa y sus hijos</h1>
<p class="lead">Manuel Salvador Álvarez Ruiz, hijo de Manuel Antonio Álvarez Vélez y de Trinidad Ruiz Velásquez, se casó con María Teresa Ruiz Maya, hija de {nm(TF)} y de {nm(TM)}. Tuvieron 18 hijos, de los cuales se criaron 11: tres varones y ocho mujeres.</p>
<div class="aside"><b>Parientes.</b> {KIN} La madre de Manuel Salvador, Trinidad Ruiz Velásquez, y la abuela materna de María Teresa, Dolores Ruiz Velásquez, eran hermanas: ambas hijas de José María Ruiz Moreno y María Mercedes Velásquez Restrepo.</div>
<figure class="hero"><img src="../docs/img/manuel-salvador-y-teresa.jpg"><figcaption>{e(H['fotos']['manuel-salvador-y-teresa.jpg'])}</figcaption></figure>
<h3>Los hijos</h3><div class="kidcards">''')
for k in kids:
    extra = []
    if k.get('spouseName'): extra.append(('Casado' if k.get('sex') == 'M' else 'Casada') + ' con ' + k['spouseName'])
    if k.get('note'): extra.append(k['note'])
    w(f'''<div class="kc"><b>{e(k['name'])}{f' <i>(«{e(k["nick"])}»)</i>' if k.get('nick') else ''}</b><span>{'Nacido' if k.get('sex') == 'M' else 'Nacida'} el {e(k['born'])}</span>{''.join(f'<span>{e(x)}</span>' for x in extra)}</div>''')
w('</div>')
sibs = [p for p in D['people'] if p.get('sibling')]
w(f'''<h3>Los hermanos de Manuel Salvador</h3><p>Hijos de Manuel Antonio Álvarez Vélez y Trinidad Ruiz Velásquez: {', '.join(e(s['name']) for s in sibs)} y el propio Manuel Salvador.</p>
<figure class="hero"><img src="../docs/img/familia-final.jpg"><figcaption>{e(H['fotos']['familia-final.jpg'])}</figcaption></figure>
</section>''')

# ---------------- 5. árbol de ascendientes
sys.path.insert(0, os.path.join(REPO, 'scripts'))
import laminas
charts, home = laminas.partition(P, ROOT)
GP = D['lineRoots']
w('<!--SP:5-->')
w(f'''<section class="chapter"><div class="chap-n">Capítulo 5</div><h1>El árbol de ascendientes</h1>
<p class="lead">El árbol parte de los once hijos: arriba están sus padres, Manuel Salvador y María Teresa, y desde ahí sube generación por generación. Cada persona tiene dos padres, cuatro abuelos, ocho bisabuelos… El árbol se organiza en seis líneas, a partir de los abuelos de Manuel Salvador y de María Teresa, y cada línea lleva su color.</p>
<div class="lines4">{''.join(f'<div><i style="background:{LCOL[i]}"></i><b>Línea {e(n)}</b><span>{e(P[g]["name"])}</span></div>' for i, (n, g) in enumerate(zip(LINES, GP)))}</div>
<p>Las cuatro primeras líneas son las de los abuelos de Manuel Salvador; Naranjo y Maya, las de los abuelos de María Teresa. Su otro abuelo, Secundino Ruiz Moreno, y su abuela Dolores Ruiz Velásquez pertenecen a la línea Ruiz, que comparte con Manuel Salvador. La línea Vélez —la de Rosalía Vélez Rivera, abuela paterna de Manuel Salvador— no tiene ascendencia registrada.</p>
<table class="gens"><thead><tr><th>Generación</th><th>Parentesco con los hijos</th><th>Posibles</th><th>Identificados</th></tr></thead><tbody>
{''.join(f'<tr><td>{g}</td><td>{gen_title(g)}</td><td>{2 ** g:,}</td><td>{by_gen[g]}</td></tr>'.replace(',', '.') for g in range(1, min(max_gen, 20) + 1))}
<tr><td>21–{max_gen}</td><td>Linajes medievales</td><td>—</td><td>{sum(c for g, c in by_gen.items() if g > 20)}</td></tr>
</tbody></table>
<p class="note">«Posibles» es el número teórico de antepasados en cada generación. La diferencia con los identificados se debe tanto a los datos que no se conocen como a los antepasados que se repiten por matrimonios entre parientes. Después de la generación 20 solo continúan algunas líneas, que llegan a la nobleza y a las casas reales de la Edad Media.</p>
<div class="fanpage"><h3>Los antepasados, en abanico</h3><p class="note">Los hijos en el centro; cada anillo es una generación más atrás (hasta la 16.ª). {' · '.join(f'<span style="color:{LCOL[i]}">●</span> {e(n)}' for i, n in enumerate(LINES))}. Los puntos con borde dorado tienen su historia en el capítulo 3.</p><svg id="fan2" viewBox="-1000 -1000 2000 2000"></svg></div>
</section>''')

# ---------------- 6. láminas
w('<!--SP:6-->')
w(f'''<section class="chapter"><div class="chap-n">Capítulo 6</div><h1>Láminas del árbol</h1>
<p class="lead">El árbol completo se presenta en {len(charts)} láminas. Cada una parte de una persona, en la parte de arriba, y baja generación por generación hacia sus antepasados: debajo de cada persona están su padre (a la izquierda) y su madre (a la derecha).</p>
<div class="howto">
  <div><span class="bx demo" style="--c:{LCOL[0]}"><span class="nm">Nombre y apellidos</span><span class="mt">año · lugar</span><span class="tg go">▸ lámina 12</span></span><p>Su ascendencia continúa en la lámina indicada, donde esta persona aparece arriba.</p></div>
  <div><span class="bx demo stub"><span class="nm">Nombre y apellidos</span><span class="tg">↺ ver lámina 5</span></span><p>Antepasado que aparece más de una vez por matrimonios entre parientes. Sus padres están en la lámina indicada.</p></div>
  <div><span class="bx demo" style="--c:{LCOL[2]}"><span class="nm">Nombre y apellidos</span><span class="mt">1690 · Medellín</span><span class="pd">Padres: Juan… y María…</span></span><p>Cuando los padres no tienen más ascendencia conocida, se escriben dentro de la caja. El año y el lugar son los que figuran en la investigación.</p></div>
</div>
<p>A la izquierda de cada fila se indica la generación contada desde los hijos (1 = Manuel Salvador y María Teresa, 2 = abuelos…). El color de cada caja corresponde a su línea; el rombo ◆ marca a los antepasados de ambos.</p>
</section><section class="laminas">''')
gen_of = lambda pid: P[pid]['gen']
def line_name(p):
    return f"Línea {LINES[p['line']]}" if p.get('line', -1) >= 0 else ''
cur_line = None
for c in charts:
    rl = P[c['root']].get('line', -1)
    if c['n'] > 1 and rl != cur_line and rl >= 0:
        w(f'<h2 class="lam-line" style="--c:{LCOL[rl]}">Línea {e(LINES[rl])}<small>Ascendientes de {e(P[GP[rl]]["name"])}</small></h2>')
        cur_line = rl
    w(laminas.render(c, P, gen_of, gen_title, col, line_name, home))
w('</section>')

# ---------------- 7. índice
w('<!--SP:7-->')
w('''<section class="chapter index"><div class="chap-n">Capítulo 7</div><h1>Índice de personas</h1>
<p class="lead">Todos los antepasados identificados, en orden alfabético. Para cada persona se indica la generación (G1 = Manuel Salvador y María Teresa, G2 = sus padres…), el año y el lugar que figuran en la investigación, y la lámina donde aparece con sus padres. El rombo ◆ marca a los antepasados de ambos.</p><div class="idx">''')
letter = None
import unicodedata
def key(s): return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()
for p in sorted([p for p in anc + [P[MANUEL], P[TERESA]] if not p.get('unknown')], key=lambda p: key(p['name'])):
    L = key(p['name'])[0].upper()
    if L != letter:
        w(f'<h4>{L}</h4>'); letter = L
    lam = home.get(p['id'])
    w(f'''<div class="ix"><i style="background:{col(p)}"></i><span class="n">{e(p['name'])}{f' <b class="lr">lám. {lam}</b>' if lam else ''}</span><span class="m">{'◆ ' if p.get('both') else ''}G{p['gen']}{' · ' + e(meta(p)) if meta(p) else ''}</span></div>''')
w('</div></section>')

# ---------------- colofón
w(f'''<section class="colophon"><p>Genealogía de los hijos de Manuel Salvador Álvarez Ruiz y María Teresa Ruiz Maya</p><p class="note">Libro elaborado a partir de la investigación familiar original: textos, fotografías, los 28 cuadros de ascendientes de Manuel Salvador y los {nT} de María Teresa. La versión digital interactiva, con buscador, árbol navegable y los cuadros originales, está en supermaty01.github.io/arbolgenealogico</p></section>''')

# --------------- datos para los gráficos
mini = {pid: {k: p[k] for k in ('name', 'father', 'mother', 'line', 'year', 'bio') if k in p} for pid, p in P.items() if p.get('gen') is not None and p['gen'] >= 0 and not p.get('child')}
tpl = open(os.path.join(REPO, 'scripts/libro_plantilla.html'), encoding='utf-8').read()
DATA_JS = 'const DATA=' + json.dumps({'root': ROOT, 'P': mini}, ensure_ascii=False) + ';'
os.makedirs(os.path.join(REPO, 'libro'), exist_ok=True)
dst = os.path.join(REPO, 'libro/libro.html')
def write_html(spacers):
    body = '\n'.join(out)
    for k in range(8):
        body = body.replace(f'<!--SP:{k}-->', '<div class="spacer"></div>' if k in spacers else '')
    open(dst, 'w', encoding='utf-8').write(tpl.replace('<!--CONTENIDO-->', body).replace('/*DATOS*/', DATA_JS))
write_html(set())
print('libro.html escrito')

if '--pdf' in sys.argv:
    import fitz
    from playwright.sync_api import sync_playwright
    pdf = os.path.join(REPO, 'libro/Genealogia-Alvarez-Ruiz.pdf')
    MARK = {0: 'PRESENTACIÓN', **{n: f'CAPÍTULO{n}' for n in range(1, 8)}}
    spacers = set()
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel='msedge')
        for it in range(12):
            write_html(spacers)
            pg = b.new_page()
            pg.goto('file:///' + dst.replace('\\', '/'))
            pg.wait_for_function('window.__listo === true', timeout=60000)
            pg.wait_for_timeout(1200)
            pg.pdf(path=pdf, prefer_css_page_size=True, print_background=True)
            pg.close()
            doc = fitz.open(pdf)
            starts = {}
            for i, page in enumerate(doc):
                t = ''.join(page.get_text().upper().split())
                for k, m in MARK.items():
                    if k not in starts and m in t and (k == 0 or 'CONTENIDO' not in t):
                        starts[k] = i + 1
            doc.close()
            bad = {k for k, pno in starts.items() if pno % 2 == 0}
            print('pasada', it + 1, 'inicios', starts, 'en página par:', sorted(bad))
            if not bad: break
            spacers ^= {min(bad)}   # se corrige en orden: lo anterior ya no cambia
        b.close()
    # número par de páginas: el colofón queda en la contracara final
    doc = fitz.open(pdf)
    if len(doc) % 2:
        r = doc[0].rect
        doc.new_page(pno=len(doc) - 1, width=r.width, height=r.height)
        doc.save(pdf + '.tmp', garbage=3, deflate=True); doc.close()
        os.replace(pdf + '.tmp', pdf)
    else:
        doc.close()
    print('PDF:', pdf, os.path.getsize(pdf) // 1024, 'KB')
