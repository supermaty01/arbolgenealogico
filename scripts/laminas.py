"""Divide el árbol de ascendientes en láminas verticales (A4 vertical) y genera su HTML.

Cada lámina parte de una persona (arriba) y baja generación por generación hacia sus antepasados,
con un máximo de W personas por fila y DMAX generaciones. Lo que no cabe continúa en otra lámina.
Los antepasados repetidos (por matrimonios entre parientes) se muestran como referencia «↺».
"""
import html

W = 7          # personas por fila (hojas del dibujo)
DMAX = 10      # generaciones por lámina
CW = 162.0     # ancho útil del dibujo (mm), además del margen de etiquetas
GUT = 10.0     # columna izquierda para la generación
S = CW / W     # ancho de cada casilla
BW = S - 2.2   # ancho de cada caja
BH = 17.0      # alto de cada caja
RH = 23.0      # alto de cada fila
HEAD = 14.0    # encabezado de la lámina

e = lambda s: html.escape(str(s or ''))


def display_tree(P, root):
    """Árbol sin ciclos: cada persona se expande una vez (BFS); las repeticiones quedan como 'stub'."""
    seen = {root}; fr = [root]; kids = {}
    while fr:
        nx = []
        for x in fr:
            kids[x] = []
            for role in ('father', 'mother'):
                q = P[x].get(role)
                if not q or q not in P: continue
                if q in seen: kids[x].append((q, role, True)); continue
                seen.add(q); kids[x].append((q, role, False)); nx.append(q)
        fr = nx
    return kids


def partition(P, root):
    kids = display_tree(P, root)
    from functools import lru_cache

    @lru_cache(maxsize=None)
    def need(pid, depth):
        """Hojas que ocupa el subárbol completo de pid si se dibuja con `depth` generaciones más."""
        ps = kids.get(pid, [])
        if depth == 0 or not ps: return 1
        return sum(1 if st else need(q, depth - 1) for q, role, st in ps)

    stack = [(root, None)]
    charts = []
    while stack:
        r, frm = stack.pop()
        levels = [[] for _ in range(DMAX)]
        conts = []

        def alloc(pid, stub, d, ci, role, budget):
            node = dict(pid=pid, stub=stub, ci=ci, role=role, cont=False)
            levels[d].append(node); idx = len(levels[d]) - 1
            ps = [] if stub else kids.get(pid, [])
            if not ps: return
            if d == DMAX - 1 or budget < len(ps):
                # si los padres no tienen más ascendencia, se escriben dentro de la caja
                if all(st or not kids.get(q) for q, role_, st in ps):
                    node['inline'] = [(q, st) for q, role_, st in ps]; return
                node['cont'] = True; conts.append(pid); return
            rem = DMAX - 1 - d
            needs = [1 if st else need(q, rem - 1) for q, role_, st in ps]
            if sum(needs) <= budget:
                give = needs
            elif len(ps) == 1:
                give = [budget]
            else:
                a_, b_ = needs
                if min(a_, b_) <= budget - 1:      # termina primero la rama pequeña
                    give = [a_, budget - a_] if a_ <= b_ else [budget - b_, b_]
                else:
                    give = [budget // 2, budget - budget // 2]
            for (q, role_, st), g in zip(ps, give):
                alloc(q, st, d + 1, idx, role_, g)

        alloc(r, False, 0, None, None, W)
        levels = [lv for lv in levels if lv]
        chart = dict(root=r, frm=frm, levels=levels)
        charts.append(chart)
        conts.sort(key=lambda q: P[q].get('line', 9) if P[q].get('line', -1) >= 0 else 9)
        for c in reversed(conts):
            stack.append((c, len(charts)))
    # numerar
    for i, c in enumerate(charts): c['n'] = i + 1
    root_of = {c['root']: c['n'] for c in charts}
    home = {}
    for c in charts:
        for d, lv in enumerate(c['levels']):
            for n in lv:
                if n['stub']: continue
                if n['pid'] in root_of: home[n['pid']] = root_of[n['pid']]
                else: home.setdefault(n['pid'], c['n'])
    for c in charts:
        for lv in c['levels']:
            for n in lv:
                for q, st in n.get('inline', []):
                    if not st: home.setdefault(q, c['n'])
    for c in charts:
        for lv in c['levels']:
            for n in lv:
                if n['cont']: n['ref'] = root_of[n['pid']]
                if n['stub']: n['ref'] = home.get(n['pid'])
    return charts, home


def layout(chart):
    L = chart['levels']
    ch = [[[j for j, m in enumerate(L[d + 1]) if m['ci'] == i] if d + 1 < len(L) else [] for i in range(len(L[d]))] for d in range(len(L))]
    pos = [[0.0] * len(lv) for lv in L]
    slot = [0]
    def place(d, i):
        kids = ch[d][i]
        if not kids:
            pos[d][i] = slot[0] * S + S / 2; slot[0] += 1
        else:
            for j in kids: place(d + 1, j)
            pos[d][i] = (pos[d + 1][kids[0]] + pos[d + 1][kids[-1]]) / 2
    place(0, 0)
    off = (CW - slot[0] * S) / 2
    return [[x + off for x in lv] for lv in pos]


def render(chart, P, gen_of, gen_title, color, line_name, home):
    pos = layout(chart)
    L = chart['levels']
    body_h = (len(L) - 1) * RH + BH
    root = P[chart['root']]
    g0 = gen_of(chart['root'])
    paths = []
    for d in range(len(L) - 1):
        y1 = d * RH + BH; y2 = (d + 1) * RH; ym = (y1 + y2) / 2
        for ci in range(len(L[d])):
            px = [pos[d + 1][j] for j, n in enumerate(L[d + 1]) if n['ci'] == ci]
            if not px: continue
            cx = pos[d][ci]
            lo, hi = min(px + [cx]), max(px + [cx])
            seg = f'M{GUT + cx:.2f},{y1:.2f}V{ym:.2f}M{GUT + lo:.2f},{ym:.2f}H{GUT + hi:.2f}'
            for x in px: seg += f'M{GUT + x:.2f},{ym:.2f}V{y2:.2f}'
            paths.append(seg)
    h = []
    sub = []
    if chart['frm']: sub.append(f'Continúa de la lámina {chart["frm"]}')
    ln = line_name(root)
    if ln: sub.append(ln)
    h.append(f'''<div class="lam" style="height:{HEAD + body_h + 3:.1f}mm"><div class="lam-h"><span class="lam-n">Lámina {chart['n']}</span>
      <span class="lam-t">Ascendientes de <b>{e(root['name'])}</b></span><span class="lam-s">{e(' · '.join(sub))}</span></div>
      <div class="lam-b" style="height:{body_h:.1f}mm"><svg viewBox="0 0 {GUT + CW} {body_h:.2f}" style="width:{GUT + CW}mm;height:{body_h:.2f}mm"><path d="{''.join(paths)}" /></svg>''')
    for d, lv in enumerate(L):
        g = g0 + d
        lbl = 'Manuel Salvador' if g == 0 else f'{g} · {gen_title(g)}'
        h.append(f'<div class="rl" style="top:{d * RH:.2f}mm;height:{BH}mm"><span>{e(lbl)}</span></div>')
        for i, n in enumerate(lv):
            p = P[n['pid']]
            x = GUT + pos[d][i] - BW / 2; y = d * RH
            cls = 'bx' + (' stub' if n['stub'] else '') + (' unk' if p.get('unknown') else '') + (' rt' if d == 0 else '')
            meta = ' · '.join(v for v in [p.get('year'), p.get('place')] if v)
            tag = ''
            if n['stub'] and n.get('ref'): tag = f'<span class="tg">↺ ver lámina {n["ref"]}</span>'
            elif n['cont']: tag = f'<span class="tg go">▸ lámina {n["ref"]}</span>'
            elif n.get('inline'):
                parts = []
                for q, st in n['inline']:
                    nm = e(P[q]['name']) if not P[q].get('unknown') else 'desconocido/a'
                    if st and home.get(q): nm += f' (↺ lám. {home[q]})'
                    parts.append(nm)
                tag = f'<span class="pd">Padres: {" y ".join(parts)}</span>'
            name = e(p['name'])
            h.append(f'<div class="{cls}" style="left:{x:.2f}mm;top:{y:.2f}mm;width:{BW:.2f}mm;min-height:{BH}mm;--c:{color(p)}">'
                     f'<span class="nm">{name}</span>{f"<span class=mt>{e(meta)}</span>" if meta and not n["stub"] else ""}{tag}</div>')
    h.append('</div></div>')
    return ''.join(h)
