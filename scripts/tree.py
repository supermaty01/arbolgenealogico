import sys, json, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parse import load, lines_of, strip_header
from bands import kind, fix_wraps
sys.stdout.reconfigure(encoding='utf-8')

SEGS = {t: [(t + 11, 0, 700 if t in (17,) else 2000)] for t in range(1, 29)}
SEGS[18] = [(28, 700, 2000), (29, 0, 2000)]
SEGS[25] = [(36, 0, 700)]
SEGS[26] = [(36, 700, 2000), (37, 0, 640)]
SEGS[27] = [(37, 640, 2000), (38, 0, 700)]
SEGS[28] = [(38, 700, 2000), (39, 0, 2000)]
CFG = {}
JUNK = re.compile(r'^(YaMi|REVISADO|CONTINUA|PASA|SIGUIENTE|COLUMNA)$')
def clean_words(ws):
    """Quita marcas de cuadro (# 9 C, 5 A, REVISADO...) que no son personas."""
    ws = sorted(ws, key=lambda w: (round(w['y']), w['x']))
    out = []; skip_until = -1
    for i, w in enumerate(ws):
        t = w['t']
        if JUNK.match(t): continue
        if w.get('pg', 0) >= 56 and (t == '17' or re.fullmatch(r'\d{1,2}(-[\w|]*)+-?|[A-D]-|-\d|\d-?', t)): continue
        if t in ('#',) or t.startswith('#'):
            # quita la etiqueta que sigue: números, letras sueltas y guiones en la misma línea
            j = i + 1; last = w
            while j < len(ws) and abs(ws[j]['y'] - w['y']) < 3 and ws[j]['x0'] - last['x1'] < 25 and re.fullmatch(r'[\dA-D\-–]{1,3}', ws[j]['t']):
                last = ws[j]; j += 1
            skip_until = j; continue
        if i < skip_until: continue
        out.append(w)
    # "9 B", "|5 A" sueltos: número + letra A-D pegados
    res = []
    k = 0
    while k < len(out):
        w = out[k]
        n = out[k + 1] if k + 1 < len(out) else None
        if n and re.fullmatch(r'\|?\d{1,2}', w['t']) and re.fullmatch(r'[A-D]', n['t']) and abs(n['y'] - w['y']) < 3 and n['x0'] - w['x1'] < 15:
            if w['t'].startswith('|'): res.append(dict(w, t='|'))
            k += 2; continue
        res.append(w); k += 1
    return res
def seg_words(pdf, tree):
    if CFG: return cfg_words(pdf, tree)
    out = []
    for k, (pg, y0, y1) in enumerate(SEGS[tree]):
        for w in load(pdf, pg):
            if y0 <= w['y'] < y1:
                w = dict(w); w['page'] = pg; w['py'] = w['y']; w['y'] += k * 1000; out.append(w)
    return out
def cfg_words(pdf, tree):
    out = []
    for k, (pg, y0, y1) in enumerate(CFG['trees'][str(tree)]):
        for w in clean_words([dict(w, pg=pg) for w in load(pdf, pg)]):
            if y0 <= w['y'] < y1:
                w = dict(w); w['page'] = pg; w['py'] = w['y']; w['y'] += k * 1000; out.append(w)
    return out
def drop_titles(lines, tree):
    out = []; kept = False
    for l in lines:
        txt = ' '.join(w['t'] for w in l)
        if txt.strip() in CFG.get('drop_lines', []):
            if str(tree) in CFG.get('keep_title', []) and not kept: kept = True; out.append(l)
            continue
        out.append(l)
    return out
def get_bands(pdf, tree):
    lines = lines_of(seg_words(pdf, tree))
    if CFG: lines = drop_titles(lines, tree)
    lines = fix_wraps(strip_header(lines))
    bands = []; cur = None; pendingY = []; prevConn = False
    lastY = None
    for l in lines:
        if lastY is not None and l[0]['y'] - lastY > 300: prevConn = True
        lastY = l[0]['y']
        ks = [kind(w) for w in l]
        hasT = any(k == 'T' for k in ks); hasY = any(k == 'Y' for k in ks)
        numline = sum(re.fullmatch(r'\d{1,2}', w['t']) is not None for w in l) > 3 and all(re.fullmatch(r'\d{1,2}|XXX|v|V', w['t']) for w in l)
        if numline:
            cur['refs'] += l; continue
        onlyCY = (not hasT) and hasY
        nY = sum(k == 'Y' for k in ks)
        newband = cur is None or (hasT and (pendingY or (hasY and (prevConn or nY >= 2))))
        yx = [w['x'] for w, k in zip(l, ks) if k == 'Y']
        twoSided = hasY and any(k == 'T' and w['x'] < min(yx) for w, k in zip(l, ks)) and any(k == 'T' and w['x'] > max(yx) for w, k in zip(l, ks))
        if CFG and cur is not None and twoSided and cur['text'] and not cur['ys']:
            newband = True  # la raíz (sin pareja) seguida directamente por la línea de sus padres
        if newband:
            cur = dict(text=[], anchors=[], ys=list(pendingY), refs=[]); bands.append(cur); pendingY = []
        for w, k in zip(l, ks):
            if k == 'C': cur['anchors'].append(w)
            elif k == 'Y':
                if onlyCY: pendingY.append(w)
                elif newband or not cur['ys']: cur['ys'].append(w)
            elif k == 'T': cur['text'].append(w)
        prevConn = any(k == 'C' for k in ks) or all(w['t'] in ('v', 'V', '.') for w in l)
    return bands

def dedup(ws, tol=9):
    ws = sorted(ws, key=lambda w: w['x']); out = []
    for w in ws:
        if out and w['x'] - out[-1]['x'] < tol:
            if w['t'] == '|': out[-1] = w
            continue
        out.append(w)
    return out

def best_split(tokens):
    a, b = min(t['x0'] for t in tokens), max(t['x1'] for t in tokens)
    best = None
    for k in range(20, 181):
        x = a + (b - a) * k / 200
        cross = sum(t['x0'] < x < t['x1'] for t in tokens)
        score = cross * 1000 + abs(x - (a + b) / 2)
        if best is None or score < best[0]: best = (score, x)
    return best[1]

def split_interval(tokens, anchors, lo, hi, n):
    an = [a['x'] for a in anchors if lo < a['x'] < hi]
    if len(an) == n: return an
    if n == 1:
        return [sum(t['x'] for t in tokens) / len(tokens) if tokens else (lo + hi) / 2]
    if len(an) > 2: return [min(an), max(an)]
    if not tokens: return [lo + (hi - lo) / 3, hi - (hi - lo) / 3]
    sx = best_split(tokens)
    L = [t['x'] for t in tokens if t['x'] < sx]; R = [t['x'] for t in tokens if t['x'] >= sx]
    return [sum(L) / len(L) if L else sx - 20, sum(R) / len(R) if R else sx + 20]

def build_persons(b):
    ys = sorted(b['ys'], key=lambda w: w['x'])
    text = b['text']
    an = dedup(b['anchors'] + [r for r in b['refs'] if r['t'] not in ('v', 'V')])
    if not ys and len([a for a in an if a['t'] in ('|', 'XXX')]) == 2 and text:
        a1, a2 = sorted(a['x'] for a in an if a['t'] in ('|', 'XXX'))
        ys = [dict(t='Y', x=(a1 + a2) / 2, y=0)]
    if not ys:
        centers =[sum(t['x'] for t in text) / len(text)] if text else []
    else:
        bounds = [-1e9] + [y['x'] for y in ys] + [1e9]
        centers = []
        for i in range(len(bounds) - 1):
            lo, hi = bounds[i], bounds[i + 1]
            n = 1 if i in (0, len(bounds) - 2) else 2
            toks = [t for t in text if lo < t['x'] < hi]
            centers += split_interval(toks, an, lo, hi, n)
    persons = [dict(cx=c, tokens=[], marks=[]) for c in centers]
    yx = [y['x'] for y in ys]
    for t in text:
        side = sum(t['x'] > y for y in yx)
        if not ys: cand = [0]
        elif side == 0: cand = [0]
        elif side == len(yx): cand = [len(persons) - 1]
        else: cand = [2 * side - 1, 2 * side]
        j = min(cand, key=lambda j: abs(persons[j]['cx'] - t['x']))
        persons[j]['tokens'].append(t)
    for a in an:
        if not persons: break
        j = min(range(len(persons)), key=lambda j: abs(persons[j]['cx'] - a['x']))
        if abs(persons[j]['cx'] - a['x']) < 60: persons[j]['marks'].append(a['t'])
    couples = [(2 * i, 2 * i + 1, ys[i]) for i in range(len(ys))]
    return persons, couples

DATE = re.compile(r'\d|^(ESP|MED|ANT|BOG|X|XX|SANTA|FE|CAL|REMD|ZARAG|RIO|NEGRO|\?|BOGOT|VENECIA|PORTUGAL|VENEZUELA|CALDAS|TOLIMA|ARNEDO|CARTAGO|POPAY|ESPA|RIONEGRO|MEDELL|PER|QUITO|PANAMA|CALI|CARTAGENA|SANTAFE|ENV|ANTIOQUIA|TUNJA|MARIQUITA|REMEDIOS|ARMA|URNIETA|GUIP|VIZCAYA|SEVILLA|C[AÁ]DIZ)', re.I)

def person_record(p):
    toks = sorted(p['tokens'], key=lambda t: (t['y'], t['x']))
    rows = []
    for t in toks:
        if rows and abs(rows[-1][-1]['y'] - t['y']) < 0.3 * t['sz'] + 0.5: rows[-1].append(t)
        else: rows.append([t])
    rows = [' '.join(w['t'] for w in sorted(r, key=lambda w: w['x'])) for r in rows]
    date = ''
    if len(rows) >= 2 and (all(DATE.match(w) for w in rows[-1].split()) or re.search(r'1[4-9]\d\d', rows[-1])):
        date = rows.pop()
    cols = {}
    for t in toks: cols[t['c']] = cols.get(t['c'], 0) + len(t['t'])
    col = max(cols, key=cols.get) if cols else '#000000'
    marks = p['marks']
    ref = [m for m in marks if m.isdigit()]
    bb = [min(t['x0'] for t in toks), min(t['py'] - t['sz'] / 2 for t in toks), max(t['x1'] for t in toks), max(t['py'] + t['sz'] / 2 for t in toks)] if toks else None
    pg = toks[0]['page'] if toks else None
    return dict(name=' '.join(rows), rows=rows, bbox=bb, page=pg, date=date, color=col, x=round(p['cx'], 1),
                y=round(min(t['y'] for t in toks), 1) if toks else 0,
                more=('|' in marks), none=('XXX' in marks), ref=int(ref[0]) if ref else None)

def parse_tree(pdf, pno, tree):
    bands = get_bands(pdf, tree)
    people = []; bandp = []; warn = []
    for bi, b in enumerate(bands):
        ps, cs = build_persons(b)
        ids = []
        for p in ps:
            r = person_record(p); r['id'] = f"T{tree}-{len(people)}"; r['band'] = bi
            r['father'] = r['mother'] = r['spouse'] = None
            people.append(r); ids.append(r['id'])
            if not r['name']: warn.append(f'band{bi} empty person {r["id"]} x={r["x"]}')
        bandp.append((ids, [(ids[a], ids[c], y['x']) for a, c, y in cs]))
    byid = {p['id']: p for p in people}
    for ids, cs in bandp:
        for h, w, _ in cs: byid[h]['spouse'] = w; byid[w]['spouse'] = h
    for k in range(1, len(bandp)):
        prev = [byid[i] for i in bandp[k - 1][0]]
        cs = bandp[k][1]
        pairs = sorted((abs(p['x'] - yx) - (30 if p['more'] else 0), ci, p['id']) for ci, (h, w, yx) in enumerate(cs) for p in prev)
        done = set(); used = set()
        for d, ci, pid in pairs:
            if ci in done or pid in used: continue
            h, w, yx = cs[ci]
            if abs(byid[pid]['x'] - yx) > 150: continue
            byid[pid]['father'] = h; byid[pid]['mother'] = w; done.add(ci); used.add(pid)
        for ci, (h, w, yx) in enumerate(cs):
            if ci not in done: warn.append(f'band{k} couple {byid[h]["name"]} & {byid[w]["name"]} has no child')
        for p in prev:
            if p['more'] and p['id'] not in used: warn.append(f'band{k-1} {p["name"]} marked | but no parents')
            if p['none'] and p['id'] in used: warn.append(f'band{k-1} {p["name"]} marked XXX but got parents')
    return people, bandp, warn

if __name__ == '__main__':
    pdf = sys.argv[1]
    allt = {}
    specs = sys.argv[2].split(',')
    if sys.argv[2].endswith('.json'):
        CFG.update(json.load(open(sys.argv[2], encoding='utf-8')))
        specs = [f"{v[0][0]}:{k}" for k, v in CFG['trees'].items()]
        if len(sys.argv) > 4: specs = [s for s in specs if s.split(':')[1] in sys.argv[4].split(',')]
    for spec in specs:
        pno, tree = map(int, spec.split(':'))
        people, bandp, warn = parse_tree(pdf, pno, tree)
        allt[tree] = dict(page=pno, people=people, warn=warn)
        print('TREE', tree, 'page', pno, 'persons', len(people))
        for w in warn: print('  WARN', w)
    if len(sys.argv) > 3:
        json.dump(allt, open(sys.argv[3], 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
