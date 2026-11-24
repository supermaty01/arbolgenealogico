"""Capa de investigación: aplica a las personas las correcciones y adiciones de contenido/investigacion.json.

Los datos del documento original no se tocan en datos/personas.json: esta capa se aplica en memoria al generar la web.
Cada hallazgo tiene una clasificación:
  CONFIRMADO   -> sus «cambios» se aplican al árbol (y el valor original queda guardado en p['orig']).
  PROBABLE     -> no se aplica: queda como nota en la ficha de la persona.
  EN CONFLICTO -> no se aplica: la nota muestra las versiones que difieren.
Los cambios de tipo «extracción» (errores de la lectura automática de los cuadros, comprobados en el cuadro original)
también se aplican: su fuente es el propio cuadro.
"""
import re, unicodedata

APLICA = {'CONFIRMADO'}


def _k(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s or '') if unicodedata.category(c) != 'Mn').lower()
    return ' '.join(re.sub(r'[^a-z0-9 ]', ' ', s).split())


class Resolver:
    def __init__(self, P):
        self.P = P
        self.refs = {}

    def find(self, sel, ctx=''):
        """Selector: {"nombre": ..., "año": opcional, "padre"/"madre"/"conyuge": nombre opcional} o {"ref": id de persona nueva}."""
        if sel is None: return None
        if isinstance(sel, str): sel = {'nombre': sel}
        if 'ref' in sel: return self.refs[sel['ref']]
        P = self.P
        if 'id' in sel:  # para gemelos exactos (mismo nombre y mismos padres); el nombre se comprueba igual
            if sel['id'] not in P or _k(P[sel['id']]['name']) != _k(sel['nombre']):
                raise SystemExit(f'investigacion.json: el selector {sel} ({ctx}) no coincide con los datos')
            return sel['id']
        c = [p for p in P.values() if _k(p.get('name')) == _k(sel['nombre'])]
        if 'año' in sel: c = [p for p in c if (p.get('year') or '').startswith(str(sel['año']))]
        for k, f in (('padre', 'father'), ('madre', 'mother')):
            if k in sel: c = [p for p in c if p.get(f) in P and _k(P[p[f]]['name']) == _k(sel[k])]
        if 'conyuge' in sel: c = [p for p in c if any(_k(P[s]['name']) == _k(sel['conyuge']) for s in p.get('spouses', []) if s in P)]
        if len(c) != 1:
            raise SystemExit(f'investigacion.json: el selector {sel} ({ctx}) encontró {len(c)} personas')
        return c[0]['id']


def _orig(p, campo, valor):
    p.setdefault('orig', {})
    if campo not in p['orig']: p['orig'][campo] = valor


def _relink(P):
    for p in P.values(): p['children'] = []
    for p in P.values():
        for k in ('father', 'mother'):
            if p.get(k) and p[k] in P and p['id'] not in P[p[k]]['children']:
                P[p[k]]['children'].append(p['id'])
    for p in P.values():
        p['spouses'] = sorted({s for s in p.get('spouses', []) if s in P and s != p['id']})
    for p in P.values():
        for s in p['spouses']:
            if p['id'] not in P[s]['spouses']: P[s]['spouses'] = sorted(set(P[s]['spouses']) | {p['id']})


def aplicar(P, INV, nuevo_id):
    """Aplica la capa sobre P (dict id -> persona). Devuelve (fuentes, hallazgos, resumen)."""
    R = Resolver(P)
    F = INV['fuentes']
    log = []
    for h in INV['hallazgos']:
        for s in h.get('fuentes', []):
            if s not in F: raise SystemExit(f'investigacion.json: {h["id"]} cita una fuente inexistente: {s}')
        if not h.get('fuentes'): raise SystemExit(f'investigacion.json: {h["id"]} no tiene fuentes')
        aplica = h['clasificacion'] in APLICA or h.get('tipo') == 'extraccion'
        pid = R.find(h['persona'], h['id']) if h.get('persona') else None
        h['_pid'] = pid
        hechos = []
        if aplica:
            for c in h.get('cambios', []):
                op = c['op']
                if op == 'nueva':
                    nid = nuevo_id(); R.refs[c['ref']] = nid
                    P[nid] = dict(id=nid, name=c['nombre'], year=c.get('year'), place=c.get('place'), raw=[], unknown=False, conq=False,
                                  father=None, mother=None, spouses=[], trees=[], children=[], variants=[], sex=c.get('sexo'),
                                  invAdded=True)
                    if c.get('hijo'):
                        ch = R.find(c['hijo'], h['id']); rol = 'father' if c.get('sexo') == 'M' else 'mother'
                        if P[ch].get(rol): raise SystemExit(f'{h["id"]}: {P[ch]["name"]} ya tiene {rol}')
                        P[ch][rol] = nid
                    if c.get('conyuge'):
                        s = R.find(c['conyuge'], h['id']); P[nid]['spouses'].append(s); P[s]['spouses'].append(nid)
                    for k, f in (('padre', 'father'), ('madre', 'mother')):
                        if c.get(k): P[nid][f] = R.find(c[k], h['id'])
                    if pid is None: pid = h['_pid'] = nid
                    else: h.setdefault('_extra', []).append(nid)
                    hechos.append(('nueva', nid))
                    continue
                tgt = R.find(c['persona'], h['id']) if c.get('persona') else pid
                p = P[tgt]
                if op == 'campo':
                    _orig(p, c['campo'], p.get(c['campo']))
                    p[c['campo']] = c['valor']
                    if c['campo'] == 'name' and p['orig']['name'] and p['orig']['name'] != c['valor']:
                        p['variants'] = sorted(set(p.get('variants', [])) | {p['orig']['name']})
                elif op == 'padres':
                    for k, f in (('padre', 'father'), ('madre', 'mother')):
                        if k in c:
                            _orig(p, f, P[p[f]]['name'] if p.get(f) in P else None)
                            p[f] = R.find(c[k], h['id']) if c[k] else None
                elif op == 'conyuge':
                    s = R.find(c['conyuge'], h['id'])
                    p['spouses'] = sorted(set(p['spouses']) | {s}); P[s]['spouses'] = sorted(set(P[s]['spouses']) | {tgt})
                elif op == 'quitar_conyuge':
                    s = R.find(c['conyuge'], h['id'])
                    _orig(p, 'spouses', [P[x]['name'] for x in p['spouses'] if x in P])
                    p['spouses'] = [x for x in p['spouses'] if x != s]; P[s]['spouses'] = [x for x in P[s]['spouses'] if x != tgt]
                elif op == 'fusionar':
                    o = R.find(c['con'], h['id'])
                    if o == tgt: raise SystemExit(f'{h["id"]}: fusión consigo mismo')
                    q = P.pop(o)
                    for k in ('father', 'mother'):
                        if not p.get(k) and q.get(k): p[k] = q[k]
                    p['spouses'] = sorted(set(p['spouses']) | set(q['spouses']))
                    p['trees'] = sorted(set(p['trees']) | set(q['trees']))
                    p['raw'] = sorted(set(p.get('raw', [])) | set(q.get('raw', [])))
                    p['variants'] = sorted((set(p.get('variants', [])) | set(q.get('variants', [])) | {q['name']}) - {p['name']})
                    for k in ('bio',):
                        if q.get(k) and not p.get(k): p[k] = q[k]
                    p['both'] = p.get('both') or q.get('both')
                    p['rootOf'] = sorted(set(p.get('rootOf', [])) | set(q.get('rootOf', [])))
                    for x in P.values():
                        for k in ('father', 'mother'):
                            if x.get(k) == o: x[k] = tgt
                        x['spouses'] = [tgt if s == o else s for s in x.get('spouses', [])]
                    p.setdefault('merged', []).append(q['name'] + (f' ({q["year"]})' if q.get('year') else ''))
                elif op == 'eliminar':
                    q = P.pop(tgt)
                    for x in P.values():
                        for k in ('father', 'mother'):
                            if x.get(k) == tgt: x[k] = None
                        x['spouses'] = [s for s in x.get('spouses', []) if s != tgt]
                    hechos.append(('eliminada', q['name']))
                    if tgt == pid: h['_pid'] = None
                    continue
                else:
                    raise SystemExit(f'{h["id"]}: operación desconocida {op}')
                hechos.append((op, tgt))
        h['_aplicado'] = bool(aplica and h.get('cambios'))
        log.append((h['id'], h['clasificacion'], h['_aplicado'], h.get('_pid')))
    _relink(P)
    # anotar en cada persona
    for h in INV['hallazgos']:
        for pid in [h.get('_pid')] + h.get('_extra', []) + [R.find(x, h['id']) for x in h.get('tambien', [])]:
            if pid and pid in P and h['id'] not in P[pid].get('inv', []):
                P[pid].setdefault('inv', []).append(h['id'])
    return log


def exportar(INV):
    """Versión compacta de los hallazgos y las fuentes para la web y el libro."""
    hs = []
    for h in INV['hallazgos']:
        hs.append({k: v for k, v in dict(id=h['id'], linea=h.get('linea'), seccion=h.get('seccion'), tipo=h.get('tipo'),
                                         c=h['clasificacion'], titulo=h['titulo'], t=h['texto'], campo=h.get('campo'),
                                         o=h.get('original'), n=h.get('nuevo'), f=h['fuentes'], a=h.get('_aplicado', False),
                                         p=h.get('_pid')).items() if v not in (None, '', [])})
    return dict(meta=INV['meta'], fuentes=INV['fuentes'], hallazgos=hs)
