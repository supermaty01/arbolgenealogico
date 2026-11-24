"""Genera docs/data/familia.json, las imágenes de los árboles originales y las fotos.

Uso: python build_site.py <personas.json> <historia.json> <docx_principal.pdf> <carpeta_media> <carpeta_docs> [<teresa.pdf> <teresa-cuadros.json>]
"""
import sys, os, json, re, unicodedata, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
import fitz
from PIL import Image
from tree import SEGS

data_path, hist_path, pdf_path, media_dir, docs = sys.argv[1:6]
T_PDF, T_CFG = (sys.argv[6], json.load(open(sys.argv[7], encoding='utf-8'))) if len(sys.argv) > 7 else (None, None)
D = json.load(open(data_path, encoding='utf-8'))
H = json.load(open(hist_path, encoding='utf-8'))
P = D['people']; manuel = D['root']; teresa_id = D.get('root2')

def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').upper()
    return [w for w in re.sub(r'[^A-Z ]', ' ', s).split() if w not in ('DE', 'DEL', 'LA', 'LOS', 'Y', 'DON', 'DONA')]
def jacc(a, b):
    A, B = set(a), set(b)
    return len(A & B) / max(1, len(A | B))

# ---------- sexo
for p in P.values(): p['sex'] = None
P[manuel]['sex'] = 'M'
if teresa_id: P[teresa_id]['sex'] = 'F'
for p in P.values():
    if p['father']: P[p['father']]['sex'] = 'M'
    if p['mother']: P[p['mother']]['sex'] = 'F'
for _ in range(3):
    for p in P.values():
        if not p['sex']:
            for s in p['spouses']:
                if P[s]['sex']: p['sex'] = 'F' if P[s]['sex'] == 'M' else 'M'

# ---------- raíz: los hijos de Manuel Salvador y María Teresa
root = 'h0'
r = P[manuel]
for p in P.values():
    g = [x for x in (p.get('genM', p['gen']), p.get('genT')) if x is not None]
    p['gen'] = 1 + min(g) if g else None
    if p.get('genM') is not None and p.get('genT') is not None: p['both'] = True
P[root] = dict(id=root, name='Hijos de Manuel Salvador y María Teresa', year=None, place=None, raw=[], unknown=False, conq=False,
               father=manuel, mother=teresa_id, spouses=[], trees=[], color='#555555', variants=[], children=[], gen=0, sex=None,
               line=-1, extra=True)

# ---------- líneas: los abuelos de Manuel Salvador y de María Teresa (bisabuelos de los hijos)
t = P[teresa_id] if teresa_id else None
LINES = ['Álvarez', 'Vélez', 'Ruiz', 'Velásquez'] + (['Naranjo', 'Maya'] if t else [])
seeds = [(P[r['father']]['father'], 0), (P[r['father']]['mother'], 1), (P[r['mother']]['father'], 2), (P[r['mother']]['mother'], 3)]
if t:
    seeds += [(P[t['father']]['father'], 2), (P[t['father']]['mother'], 4), (P[t['mother']]['father'], 5), (P[t['mother']]['mother'], 2)]
gp = [g for g, _ in seeds[:4]] + ([seeds[5][0], seeds[6][0]] if t else [])
line = {root: -1, manuel: -2, r['father']: -2, r['mother']: -2}
if t: line.update({teresa_id: -3, t['father']: -3, t['mother']: -3})
queue = []
for g, i in seeds:
    if g not in line: line[g] = i; queue.append((g, i))
while queue:
    x, i = queue.pop(0)
    for k in ('father', 'mother'):
        y = P[x][k]
        if y and y not in line:
            line[y] = i; queue.append((y, i))
for p in P.values(): p['line'] = line.get(p['id'])
for i, n in enumerate(LINES): print('línea', n, sum(1 for p in P.values() if p['line'] == i))

# ---------- biografías del linaje
bios = {}
for sec in H['linaje']:
    target = norm(sec['persona'])
    best = max(P.values(), key=lambda p: (jacc(norm(p['name']), target), -(p['gen'] or 99)))
    if jacc(norm(best['name']), target) < 0.5:
        print('WARN bio sin persona:', sec['persona'], '->', best['name'])
    bios[best['id']] = sec['n']
    best['bio'] = sec['n']
    print('bio', sec['n'], sec['persona'], '->', best['id'], best['name'])

# ---------- descendientes y hermanos (de la narrativa)
def add(pid, **kw):
    base = dict(id=pid, name='', year=None, place=None, raw=[], unknown=False, conq=False, father=None, mother=None,
                spouses=[], trees=[], color='#555555', variants=[], children=[], gen=None, sex=None, line=None, extra=True)
    base.update(kw); P[pid] = base; return base
if teresa_id:
    teresa = P[teresa_id]
else:
    teresa = add('d0', name=H['conyuge_raiz']['nombre'], sex='F', gen=1, line=-3)
    teresa_id = 'd0'; P[root]['mother'] = 'd0'
P[manuel]['spouses'] = sorted(set(P[manuel]['spouses']) | {teresa_id}); teresa['spouses'] = sorted(set(teresa['spouses']) | {manuel})
for i, h in enumerate(H['hijos_raiz']):
    sex = 'F' if h['nombre'].split()[0].endswith('a') or h['nombre'].split()[0] in ('Judith', 'Rocío', 'Edelmira', 'Otilia', 'Concha') else 'M'
    if h['nombre'].split()[0] in ('Horacio', 'Bernardo', 'Hernán'): sex = 'M'
    y, m, d = h['nacimiento'].split('-')
    c = add(f'd{i+1}', name=h['nombre'], sex=sex, father=manuel, mother=teresa_id, gen=0, line=-1, child=True,
            born=f'{int(d)}/{int(m)}/{y}', year=y, nick=h.get('apodo'), spouseName=h.get('conyuge'), note=h.get('nota'))
    P[manuel]['children'].append(c['id']); teresa['children'].append(c['id']); P[root]['children'].append(c['id'])
fa, mo = r['father'], r['mother']
for i, n in enumerate(H['hermanos_raiz']):
    sex = 'F' if n.split()[0] in ('Mercedes', 'Anatolia') else 'M'
    c = add(f's{i}', name=n, sex=sex, father=fa, mother=mo, gen=1, line=-2, sibling=True)
    P[fa]['children'].append(c['id']); P[mo]['children'].append(c['id'])

# ---------- árboles originales
os.makedirs(f'{docs}/arboles', exist_ok=True)
doc = fitz.open(pdf_path)
trees = []
occ_by_tree = collections.defaultdict(list)
for p in P.values():
    for t in p['trees']: occ_by_tree[t].append(p['id'])
def render_tree(doc, segs, fn):
    if os.environ.get('SKIP_IMG') and os.path.exists(f'{docs}/arboles/{fn}.webp'):
        return Image.open(f'{docs}/arboles/{fn}.webp').size
    parts = []
    for pg, y0, y1 in segs:
        page = doc[pg - 1]
        allw = page.get_text('words')
        hdr = [(w[1] + w[3]) / 2 for w in allw if 'ASCEND' in w[4]]
        def is_hdr(w):
            y = (w[1] + w[3]) / 2
            return w[4] == 'YaMi' or any(abs(y - h) < 8 or (h < y < h + 32 and re.fullmatch(r'(TOTAL)?\d{3,4}', w[4])) for h in hdr)
        words = [w for w in allw if y0 <= (w[1] + w[3]) / 2 < y1 and not is_hdr(w)]
        if not words: continue
        bx0 = max(0, min(w[0] for w in words) - 12); bx1 = min(page.rect.width, max(w[2] for w in words) + 12)
        by0 = max(0, min(w[1] for w in words) - 12); by1 = min(page.rect.height, max(w[3] for w in words) + 12)
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(bx0, by0, bx1, by1))
        parts.append(Image.frombytes('RGB', (pix.width, pix.height), pix.samples))
    W = max(im.width for im in parts); Hh = sum(im.height for im in parts)
    canvas = Image.new('RGB', (W, Hh), 'white'); y = 0
    for im in parts: canvas.paste(im, (0, y)); y += im.height
    canvas.save(f'{docs}/arboles/{fn}.webp', 'WEBP', quality=82, method=6)
    thumb = canvas.copy(); thumb.thumbnail((640, 640)); thumb.save(f'{docs}/arboles/{fn}-mini.webp', 'WEBP', quality=75)
    return W, Hh
def tree_entry(t, fn, W, Hh, label, side):
    roots = [i for i in occ_by_tree[t] if t in P[i].get('rootOf', [])]
    roots.sort(key=lambda i: int(i[1:]) if i[1:].isdigit() else 9999)
    print('árbol', label, W, Hh, [P[i]['name'] for i in roots])
    return dict(n=t, label=label, side=side, img=fn + '.webp', w=W, h=Hh, roots=roots, count=len(occ_by_tree[t]))
for t in range(1, 29):
    fn = f'arbol-{t:02d}'
    W, Hh = render_tree(doc, SEGS[t], fn)
    trees.append(tree_entry(t, fn, W, Hh, str(t), 'M'))
if T_PDF:
    tdoc = fitz.open(T_PDF)
    lab = T_CFG['labels']
    def lkey(k):
        m = re.match(r'(\d+)(.*)', lab[k]); return (int(m.group(1)), m.group(2))
    for k in sorted(T_CFG['trees'], key=lkey):
        fn = f'teresa-{lab[k].lower()}'
        W, Hh = render_tree(tdoc, T_CFG['trees'][k], fn)
        trees.append(dict(tree_entry(int(k), fn, W, Hh, lab[k], 'T'), **({'title': T_CFG['titles'][k]} if k in T_CFG.get('titles', {}) else {})))
    for k, segs in T_CFG.get('solo_imagen', {}).items():
        pg = int(k) - 55
        fn = f'teresa-parte2-p{pg:02d}'
        W, Hh = render_tree(tdoc, segs, fn)
        trees.append(dict(n=2000 + int(k), label=f'P2-{pg}', side='T', img=fn + '.webp', w=W, h=Hh, roots=[], count=0,
                          name=f'Parte 2, página {pg}', title='Página medieval (solo imagen)'))

# ---------- fotos
os.makedirs(f'{docs}/img', exist_ok=True)
FOTOS = {'image4.png': 'manuel-antonio-1.jpg', 'image3.png': 'manuel-antonio-2.jpg',
         'image2.png': 'manuel-salvador-y-teresa.jpg', 'image1.png': 'familia-final.jpg'}
for src, dst in FOTOS.items():
    im = Image.open(os.path.join(media_dir, src)).convert('RGB')
    if src == 'image3.png':  # recorta los íconos de la app que quedaron en el borde derecho
        im = im.crop((0, 0, int(im.width * 0.90), im.height))
    im.thumbnail((1400, 1400)); im.save(f'{docs}/img/{dst}', 'JPEG', quality=86, optimize=True)

# ---------- salida compacta
KEEP = ['id', 'name', 'year', 'place', 'raw', 'unknown', 'conq', 'father', 'mother', 'spouses', 'trees', 'children',
        'gen', 'genM', 'genT', 'both', 'sex', 'line', 'variants', 'bio', 'extra', 'born', 'nick', 'spouseName', 'note', 'sibling', 'child']
people = []
for p in P.values():
    q = {k: p[k] for k in KEEP if k in p and p[k] is not None and p[k] is not False and p[k] != [] and p[k] != ''}
    people.append(q)
out = dict(root=root, manuel=manuel, teresa=teresa_id, lines=LINES, lineRoots=gp, people=people, trees=trees, historia=H)
json.dump(out, open(f'{docs}/data/familia.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('ambos', sum(1 for p in P.values() if p.get('both')), 'personas', len(people), 'conectadas', sum(1 for p in P.values() if p.get('gen') is not None))
