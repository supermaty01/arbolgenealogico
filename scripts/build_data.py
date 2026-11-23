"""Convierte trees.json (salida del parser) en un grafo unificado de personas."""
import sys, json, re, unicodedata, collections
sys.stdout.reconfigure(encoding='utf-8')
T = json.load(open(sys.argv[1], encoding='utf-8'))
OUT = sys.argv[2]

def strip_acc(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

PLACES = [
    (r'^SANTA[\. ]?FE', 'Santa Fe de Antioquia'), (r'^ZARAG', 'Zaragoza (Antioquia)'),
    (r'^REM', 'Remedios (Antioquia)'), (r'^RIO ?NEGRO', 'Rionegro'), (r'^MED', 'Medellín'),
    (r'^ESP', 'España'), (r'^ANTIOQUIA', 'Antioquia'), (r'^ANT', 'Antioquia'), (r'^BOG', 'Bogotá'),
    (r'^CALDAS|^CALD', 'Caldas'), (r'^CALLE', None), (r'^CAL', 'Cali'), (r'^TOL', 'Tolima'),
    (r'^CUN', 'Cundinamarca'), (r'^VALLE', 'Valle del Cauca'), (r'^PORTUGAL', 'Portugal'),
    (r'^VEN[EZ]', 'Venezuela'), (r'^VENECIA', 'Venecia'), (r'^TUNJA', 'Tunja'),
    (r'^ARNEDO', 'Arnedo (España)'), (r'^ARMA', 'Arma (Antioquia)'), (r'^CARTAGO', 'Cartago'), (r'^POPAY', 'Popayán'), (r'^URNIETA', 'Urnieta (España)'), (r'^COL', 'Colombia'), (r'^SAN$', 'Santa Fe de Antioquia'),
]
PLACE_TOKEN = re.compile(r'^(ESP|MED|ANT|BOG|SANTA|FE|ZARAG|REM|CAL|CALD|TOL|CUN|CUND|VALLE|VENEZ|VENZ|VENEZU|VENEZUE|VENEZUL|COL)[\.\-]', re.I)

ACC = {w: w2 for w2 in '''Álvarez Vélez Peláez Gómez González Pérez López García Velásquez Velázquez Sánchez Martínez
Rodríguez Hernández Fernández Gutiérrez Díaz Ramírez Jiménez Núñez María José Jerónimo Jerónima Cristóbal Nicolás Tomás
Matías Lucía Inés Bárbara Ángel Andrés Joaquín Agustín Martín Sebastián Fabián Bartolomé Mencía Rosalía Castrillón
Mejía Blandón Quirós Benítez Vásquez Suárez Ríos Ávila Bernaldo Ordóñez Cortés Tabares Colmenero Muñoz Ortíz
Juliana Tomasa Simón Ramón Julián Germán Jesús Ignacia Andrés Ascensión Concepción Encarnación Asunción Rafael
Damián Adrián Gaspar Baltasar Melchor Ginés Sebastiana Antonia Cecilia Josefa Manuela Rodrigo Benítez Cataño Saavedra Calle'''.split()
       for w in [strip_acc(w2).upper()]}
for k in ['CORTES', 'ORTIZ', 'BERNALDO', 'TABARES', 'COLMENERO', 'RODRIGO', 'CECILIA', 'JOSEFA', 'MANUELA', 'ANTONIA', 'TOMASA', 'SEBASTIANA', 'JULIANA', 'IGNACIA', 'RAFAEL', 'GASPAR', 'BALTASAR', 'MELCHOR', 'CATAÑO', 'CATANO', 'SAAVEDRA', 'CALLE']:
    ACC.pop(k, None)
ACC['CORTES'] = 'Cortés'
LOWER = {'DE', 'DEL', 'LA', 'LAS', 'LOS', 'Y', 'E'}

def title(tok):
    up = tok.upper()
    if up in LOWER: return up.lower()
    if strip_acc(up) in ACC: return ACC[strip_acc(up)]
    parts = re.split(r"([\-'’])", tok)
    return ''.join(p[:1].upper() + p[1:].lower() if p and p not in "-'’" else p for p in parts)

def parse_place(s):
    s = s.strip(' .|').upper()
    if not s or s in ('X', 'XX', 'XXX', '?'): return None, None
    years = re.findall(r'(1[4-9]\d\d)', s)
    place = None
    s2 = re.sub(r'[\d\.\-\|]+', ' ', s).strip()
    for tok in [s2] + s2.split():
        for pat, name in PLACES:
            if re.match(pat, tok):
                place = name; break
        if place: break
    yr = '–'.join(years) if years else None
    return place, yr

# ---- correcciones puntuales del parseo
def fixups(T):
    for t, v in T.items():
        P = v['people']; by = {p['id']: p for p in P}
        for p in P:
            p['name'] = p['name'].replace('DOMING0', 'DOMINGO')
        if t == '12':
            n = by['T12-1']
            if 'ANTONIO' in n['name']:
                new = dict(n); new['id'] = 'T12-x1'; new['name'] = 'ANTONIO VELEZ PELAEZ'; new['spouse'] = None
                n['name'] = 'NICOLASA MONTOYA'; n['father'] = n['mother'] = None
                P.append(new)
        lasso_needed = False
        for p in list(P):
            toks = p['name'].split()
            if 'LASSO' in toks and not p['name'].startswith('CATALINA LASSO'):
                rm = ['LASSO', 'VEGA']
                toks2 = list(toks)
                for r in rm:
                    if r in toks2: toks2.remove(r)
                if toks2.count('CATALINA') >= 1 and toks2[0] == 'CATALINA' and ('GÓMEZ' in toks2 or 'GOMEZ' in toks2) and 'REDONDO' not in toks2:
                    toks2.remove('CATALINA')
                elif toks2.count('CATALINA') >= 2:
                    toks2.remove('CATALINA')
                s2 = ' '.join(toks2).replace(' DE LA', '').replace('DE LA ', '')
                p['name'] = s2.strip(); lasso_needed = True
        if lasso_needed:
            for p in list(P):
                if re.search(r'JUANA ISABEL (DE LOS )?R[IÍ]OS', p['name']) and not p['mother']:
                    new = dict(id=p['id'] + 'm', name='CATALINA LASSO DE LA VEGA', rows=[], date='ESP', color=p['color'],
                               x=p['x'], y=p['y'] + 30, band=p['band'] + 1, father=None, mother=None, spouse=None,
                               more=False, none=True, ref=None, bbox=None, page=None)
                    P.append(new); p['mother'] = new['id']
fixups(T)
clean_names = {}
persons = []  # occurrences
for t, v in T.items():
    for p in v['people']:
        toks = p['name'].replace('(CONQUISTADOR)', '').split()
        extra = []
        title_prefix = ''
        keep = []
        for i, w in enumerate(toks):
            W = w.upper()
            if W in ('.', '..', ',', '(', ')', 'Y', 'E') and i > 0: continue
            if re.fullmatch(r'\d+', W) and len(W) != 4: continue
            if re.search(r'\d', W) or PLACE_TOKEN.match(W) or W in ('VENEZU.', 'VENZ.', 'VENEZ.', 'VENEZUE.', 'VENEZUL.', '.X'):
                extra.append(W); continue
            if W == 'CAP.': title_prefix = 'Capitán '; continue
            keep.append(w.strip('.,') if W not in ('J.',) else w)
        keep = [w for w in keep if w.upper() not in ('X', 'XX')]
        while keep and (keep[-1].upper() in ('?', '.', 'ESP', 'COL', 'MED', 'ANT', 'BOG') or (len(keep[-1]) == 1 and len(keep) > 1)):
            extra.append(keep.pop().upper())
        if len(keep) >= 2 and keep[-2].upper() == 'ARMA' and keep[-1].upper() in ('VIEJA', 'VIEJO'):
            keep = keep[:-2]; extra.insert(0, 'ARMA')
        conq = '(CONQUISTADOR)' in p['name']
        name_raw = ' '.join(keep)
        unknown = not keep or name_raw in ('?',)
        date_raw = ' '.join([p['date']] + extra).strip()
        place, year = parse_place(date_raw)
        disp = title_prefix + ' '.join(title(w) for w in keep) if not unknown else 'Desconocido/a'
        key = ' '.join(x for x in strip_acc(name_raw.upper()).replace('-', ' ').split() if x not in LOWER) if not unknown else None
        persons.append(dict(oid=p['id'], tree=int(t), band=p['band'], name=disp, key=key, unknown=unknown,
                            raw=p['name'], date_raw=date_raw, place=place, year=year, color=p['color'],
                            father=p['father'], mother=p['mother'], spouse=p['spouse'], ref=p['ref'],
                            none=p['none'], conq=conq))
occ = {p['oid']: p for p in persons}

# ---- union-find
par = {p['oid']: p['oid'] for p in persons}
def find(a):
    while par[a] != a:
        par[a] = par[par[a]]; a = par[a]
    return a
def union(a, b):
    a, b = find(a), find(b)
    if a != b: par[b] = a

def years_ok(a, b):
    ya, yb = occ[a]['year'], occ[b]['year']
    if not ya or not yb: return True
    return abs(int(ya[:4]) - int(yb[:4])) <= 3

# link tree-1 leaves (ref N) to roots of tree N
def jacc(a, b):
    A, B = set(a.split()), set(b.split())
    return len(A & B) / max(1, len(A | B))
for p in persons:
    if p['tree'] == 1 and p['ref'] and str(p['ref']) in T and p['key']:
        cands = [q for q in persons if q['tree'] == p['ref'] and q['band'] <= 1 and q['key']]
        if not cands: continue
        best = max(cands, key=lambda q: (jacc(p['key'], q['key']), -q['band']))
        if jacc(p['key'], best['key']) >= 0.34:
            union(best['oid'], p['oid']); print('link', p['name'], '->', p['ref'], best['name'], best['oid'])
        else:
            print('no match for leaf', p['name'], '->', p['ref'], [c['name'] for c in cands])

# merge by identical key (>= 2 tokens) with compatible years
groups = collections.defaultdict(list)
for p in persons:
    if p['key'] and len(p['key'].split()) >= 2:
        groups[p['key']].append(p['oid'])
def kname(oid):
    return occ[oid]['key'] if oid and oid in occ and occ[oid]['key'] else None
def same(a, b, th=0.5):
    return a is not None and b is not None and jacc(a, b) >= th
def evidence(a, b):
    A, B = occ[a], occ[b]
    if A['year'] and B['year'] and abs(int(A['year'][:4]) - int(B['year'][:4])) <= 3: return True
    if same(kname(A['spouse']), kname(B['spouse'])): return True
    if same(kname(A['father']), kname(B['father'])) and same(kname(A['mother']), kname(B['mother'])): return True
    return False
def conflict(a, b):
    A, B = occ[a], occ[b]
    if not years_ok(a, b): return True
    for k in ('father', 'mother', 'spouse'):
        ka, kb = kname(A[k]), kname(B[k])
        if ka and kb and jacc(ka, kb) < (0.5 if k == 'spouse' else 0.25): return True
    return False
def members():
    m = collections.defaultdict(list)
    for p in persons: m[find(p['oid'])].append(p['oid'])
    return m
def cluster_conflict(ra, rb, M):
    for x in M[ra]:
        for y in M[rb]:
            X, Y = occ[x], occ[y]
            if not years_ok(x, y): return True
            ka, kb = kname(X['spouse']), kname(Y['spouse'])
            if ka and kb and jacc(ka, kb) < 0.3 and not (X['unknown'] or Y['unknown']): return True
    return False
for k, ids in groups.items():
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            if evidence(ids[i], ids[j]) and not conflict(ids[i], ids[j]):
                M = members()
                if not cluster_conflict(find(ids[i]), find(ids[j]), M):
                    union(ids[i], ids[j])

def similar(a, b):
    if a['unknown'] or b['unknown']: return True
    if not (a['key'] and b['key']): return False
    ka, kb = a['key'].split(), b['key'].split()
    return jacc(a['key'], b['key']) >= 0.5 or (ka[0] == kb[0] and jacc(a['key'], b['key']) >= 0.3) or len(set(ka[1:]) & set(kb[1:])) >= 2
# second pass: parents (same role) and spouses of the same merged person are the same person when names are similar
changed = True
while changed:
    changed = False
    M = members()
    rel = collections.defaultdict(list)
    for p in persons:
        r = find(p['oid'])
        if p['father']: rel[(r, 'f')].append(p['father'])
        if p['mother']: rel[(r, 'm')].append(p['mother'])
        if p['spouse']: rel[(r, 's')].append(p['spouse'])
    for (c, role), lst in rel.items():
        roots = list({find(x) for x in lst})
        for i in range(1, len(roots)):
            if find(roots[0]) == find(roots[i]): continue
            a, b = occ[roots[0]], occ[roots[i]]
            if role == 's' and len({find(x) for x in lst}) > 1 and not similar(a, b): continue
            if similar(a, b) and not cluster_conflict(find(roots[0]), find(roots[i]), M):
                union(roots[0], roots[i]); changed = True; M = members()

# ---- orphan pass: clusters not reachable from the root get merged into a similar reachable "twin"
def reach():
    cnt = collections.defaultdict(collections.Counter)
    for p in persons:
        r = find(p['oid'])
        for k in ('father', 'mother'):
            if p[k]: cnt[(r, k)][find(p[k])] += 1
    rel = collections.defaultdict(set)
    for (r, k), c in cnt.items(): rel[r].add(c.most_common(1)[0][0])
    root = find(next(p for p in persons if p['tree'] == 1 and p['band'] == 0)['oid'])
    seen = {root}; st = [root]
    while st:
        x = st.pop()
        for y in rel[x]:
            if y not in seen: seen.add(y); st.append(y)
    return seen
for it in range(4):
    R = reach()
    M = members()
    spouse_of = collections.defaultdict(set); child_of = collections.defaultdict(set)
    for p in persons:
        if p['spouse']: spouse_of[find(p['oid'])].add(find(p['spouse']))
        for k in ('father', 'mother'):
            if p[k]: child_of[find(p[k])].add(find(p['oid']))
    merged = 0
    for r in list(M):
        if find(r) != r or r in R: continue
        o = occ[r]
        cands = set()
        for s_ in spouse_of[r]:
            for t in spouse_of[find(s_)]:
                if find(t) != r: cands.add(find(t))
        for c in child_of[r]:
            for q in persons:
                if find(q['oid']) == find(c):
                    for k in ('father', 'mother'):
                        if q[k] and find(q[k]) != r: cands.add(find(q[k]))
        cands = [c for c in cands if c in R and similar(o, occ[c])]
        if o['key']:
            cands = [c for c in cands if occ[c]['key']] or cands
        if len(cands) >= 1:
            best = max(cands, key=lambda c: jacc(o['key'] or '', occ[c]['key'] or ''))
            union(best, r); merged += 1
    if not merged: break

# ---- build unified people
clusters = collections.defaultdict(list)
for p in persons: clusters[find(p['oid'])].append(p)
root_occ = next(p for p in persons if p['tree'] == 1 and p['band'] == 0)
ids = {}
def pid_of(oid): return ids[find(oid)]
order = sorted(clusters, key=lambda r: (min(o['tree'] for o in clusters[r]), min(o['band'] for o in clusters[r])))
for n, r in enumerate(order): ids[r] = f'p{n}'
people = {}
for r in order:
    oc = clusters[r]
    named = [o for o in oc if not o['unknown']]
    name = collections.Counter(o['name'] for o in named).most_common(1)[0][0] if named else 'Desconocido/a'
    # prefer the longest variant among the most common ones
    if named:
        cnt = collections.Counter(o['name'] for o in named)
        top = max(cnt.values())
        name = max([n for n, c in cnt.items() if c >= max(1, top - 1)], key=len)
    best = sorted(oc, key=lambda o: (bool(o['year']) and bool(o['place']), bool(o['year']), bool(o['place'])), reverse=True)[0]
    year = best['year'] or next((o['year'] for o in oc if o['year']), None)
    place = best['place'] or next((o['place'] for o in oc if o['place']), None)
    fcnt = collections.Counter(find(o['father']) for o in oc if o['father'])
    mcnt = collections.Counter(find(o['mother']) for o in oc if o['mother'])
    spouses = sorted({ids[find(o['spouse'])] for o in oc if o['spouse']} - {ids[r]})
    people[ids[r]] = dict(id=ids[r], name=name, year=year, place=place,
                          raw=sorted({o['date_raw'] for o in oc if o['date_raw']}),
                          unknown=not named, conq=any(o['conq'] for o in oc),
                          father=ids[fcnt.most_common(1)[0][0]] if fcnt else None,
                          mother=ids[mcnt.most_common(1)[0][0]] if mcnt else None,
                          spouses=spouses, trees=sorted({o['tree'] for o in oc}), rootOf=sorted({o['tree'] for o in oc if o['band'] == 0}),
                          color=collections.Counter(o['color'] for o in oc).most_common(1)[0][0],
                          variants=sorted({o['name'] for o in named} - {name}))
# guard against cycles (a person being their own ancestor)
def anc_has(pid, target, seen=None):
    seen = seen or set()
    stack = [pid]
    while stack:
        x = stack.pop()
        if x == target: return True
        if x in seen: continue
        seen.add(x)
        for k in ('father', 'mother'):
            if people[x][k]: stack.append(people[x][k])
    return False
for p in people.values():
    for k in ('father', 'mother'):
        if p[k] and anc_has(p[k], p['id']):
            print('cycle removed', p['name'], k); p[k] = None
for p in people.values(): p['children'] = []
for p in people.values():
    for k in ('father', 'mother'):
        if p[k]: people[p[k]]['children'].append(p['id'])
root = pid_of(root_occ['oid'])
# generation = shortest distance from root
gen = {root: 0}; q = [root]
while q:
    x = q.pop(0)
    for k in ('father', 'mother'):
        y = people[x][k]
        if y and y not in gen: gen[y] = gen[x] + 1; q.append(y)
for p in people.values(): p['gen'] = gen.get(p['id'])
orphans = [p['name'] for p in people.values() if p['gen'] is None]
print('people', len(people), 'occurrences', len(persons), 'not connected to root', len(orphans))
print(orphans[:40])
tc = collections.Counter(t for p in people.values() if p['gen'] is None for t in p['trees'])
print('orphans by tree', tc)
json.dump(dict(root=root, people=people), open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
