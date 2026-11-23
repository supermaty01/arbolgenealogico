"""Genera docs/data/familia.json, las imágenes de los árboles originales y las fotos.

Uso: python build_site.py <personas.json> <historia.json> <docx_principal.pdf> <carpeta_media> <carpeta_docs>
"""
import sys, os, json, re, unicodedata, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding='utf-8')
import fitz
from PIL import Image
from tree import SEGS

data_path, hist_path, pdf_path, media_dir, docs = sys.argv[1:6]
D = json.load(open(data_path, encoding='utf-8'))
H = json.load(open(hist_path, encoding='utf-8'))
P = D['people']; root = D['root']

def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').upper()
    return [w for w in re.sub(r'[^A-Z ]', ' ', s).split() if w not in ('DE', 'DEL', 'LA', 'LOS', 'Y', 'DON', 'DONA')]
def jacc(a, b):
    A, B = set(a), set(b)
    return len(A & B) / max(1, len(A | B))

# ---------- sexo
for p in P.values(): p['sex'] = None
P[root]['sex'] = 'M'
for p in P.values():
    if p['father']: P[p['father']]['sex'] = 'M'
    if p['mother']: P[p['mother']]['sex'] = 'F'
for _ in range(3):
    for p in P.values():
        if not p['sex']:
            for s in p['spouses']:
                if P[s]['sex']: p['sex'] = 'F' if P[s]['sex'] == 'M' else 'M'

# ---------- línea (cuatro abuelos)
LINES = []
r = P[root]
gp = [(P[r['father']]['father'], 'Álvarez'), (P[r['father']]['mother'], 'Vélez'),
      (P[r['mother']]['father'], 'Ruiz'), (P[r['mother']]['mother'], 'Velásquez')]
line = {root: -1, r['father']: -2, r['mother']: -3}
queue = [(g, i) for i, (g, _) in enumerate(gp)]
for g, i in queue: line.setdefault(g, i)
while queue:
    x, i = queue.pop(0)
    for k in ('father', 'mother'):
        y = P[x][k]
        if y and y not in line:
            line[y] = i; queue.append((y, i))
for p in P.values(): p['line'] = line.get(p['id'])

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
teresa = add('d0', name=H['conyuge_raiz']['nombre'], sex='F', spouses=[root])
P[root]['spouses'] = [teresa['id']]
for i, h in enumerate(H['hijos_raiz']):
    sex = 'F' if h['nombre'].split()[0].endswith('a') or h['nombre'].split()[0] in ('Judith', 'Rocío', 'Edelmira', 'Otilia', 'Concha') else 'M'
    if h['nombre'].split()[0] in ('Horacio', 'Bernardo', 'Hernán'): sex = 'M'
    y, m, d = h['nacimiento'].split('-')
    c = add(f'd{i+1}', name=h['nombre'], sex=sex, father=root, mother='d0', gen=-1,
            born=f'{int(d)}/{int(m)}/{y}', year=y, nick=h.get('apodo'), spouseName=h.get('conyuge'), note=h.get('nota'))
    P[root]['children'].append(c['id']); teresa['children'].append(c['id'])
fa, mo = r['father'], r['mother']
for i, n in enumerate(H['hermanos_raiz']):
    sex = 'F' if n.split()[0] in ('Mercedes', 'Anatolia') else 'M'
    c = add(f's{i}', name=n, sex=sex, father=fa, mother=mo, gen=0, sibling=True)
    P[fa]['children'].append(c['id']); P[mo]['children'].append(c['id'])

# ---------- árboles originales
os.makedirs(f'{docs}/arboles', exist_ok=True)
doc = fitz.open(pdf_path)
trees = []
occ_by_tree = collections.defaultdict(list)
for p in P.values():
    for t in p['trees']: occ_by_tree[t].append(p['id'])
for t in range(1, 29):
    parts = []
    for pg, y0, y1 in SEGS[t]:
        page = doc[pg - 1]
        allw = page.get_text('words')
        hdr = [(w[1] + w[3]) / 2 for w in allw if 'ASCEND' in w[4]]
        def is_hdr(w):
            y = (w[1] + w[3]) / 2
            return any(abs(y - h) < 8 or (h < y < h + 32 and re.fullmatch(r'(TOTAL)?\d{3,4}', w[4])) for h in hdr)
        words = [w for w in allw if y0 <= (w[1] + w[3]) / 2 < y1 and not is_hdr(w)]
        if not words: continue
        bx0 = max(0, min(w[0] for w in words) - 12); bx1 = min(page.rect.width, max(w[2] for w in words) + 12)
        by0 = max(0, min(w[1] for w in words) - 12); by1 = min(page.rect.height, max(w[3] for w in words) + 12)
        pix = page.get_pixmap(matrix=fitz.Matrix(3, 3), clip=fitz.Rect(bx0, by0, bx1, by1))
        parts.append(Image.frombytes('RGB', (pix.width, pix.height), pix.samples))
    W = max(im.width for im in parts); Hh = sum(im.height for im in parts)
    canvas = Image.new('RGB', (W, Hh), 'white'); y = 0
    for im in parts: canvas.paste(im, (0, y)); y += im.height
    fn = f'arbol-{t:02d}.webp'
    canvas.save(f'{docs}/arboles/{fn}', 'WEBP', quality=82, method=6)
    thumb = canvas.copy(); thumb.thumbnail((640, 640)); thumb.save(f'{docs}/arboles/arbol-{t:02d}-mini.webp', 'WEBP', quality=75)
    # raíz del árbol: personas de menor generación en ese árbol
    roots = [i for i in occ_by_tree[t] if t in P[i].get('rootOf', [])]
    roots.sort(key=lambda i: int(i[1:]) if i[1:].isdigit() else 9999)
    trees.append(dict(n=t, img=fn, w=W, h=Hh, roots=roots, count=len(occ_by_tree[t])))
    print('árbol', t, W, Hh, [P[i]['name'] for i in roots])

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
        'gen', 'sex', 'line', 'variants', 'bio', 'extra', 'born', 'nick', 'spouseName', 'note', 'sibling']
people = []
for p in P.values():
    q = {k: p[k] for k in KEEP if k in p and p[k] is not None and p[k] is not False and p[k] != [] and p[k] != ''}
    people.append(q)
out = dict(root=root, lines=[n for _, n in gp], people=people, trees=trees, historia=H)
json.dump(out, open(f'{docs}/data/familia.json', 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print('personas', len(people), 'conectadas', sum(1 for p in P.values() if p.get('gen') is not None))
