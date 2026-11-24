"""Genera investigacion/HALLAZGOS.md: la cabecera escrita a mano más la lista de hallazgos de contenido/investigacion.json.

Uso: python informe_investigacion.py <carpeta_repo>
"""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
R = os.path.abspath(sys.argv[1])
INV = json.load(open(os.path.join(R, 'contenido/investigacion.json'), encoding='utf-8'))
FAM = json.load(open(os.path.join(R, 'docs/data/familia.json'), encoding='utf-8'))
P = {p['id']: p for p in FAM['people']}
X = {h['id']: h for h in FAM['investigacion']['hallazgos']}
out = [open(os.path.join(R, 'investigacion/informe_cabecera.md'), encoding='utf-8').read().rstrip(), '']
F = INV['fuentes']
def src(k):
    f = F[k]; u = f['u']
    if u.startswith('arboles/'): u = '../docs/' + u
    elif u.startswith('#'): return f['t']
    return f"[{f['t']}]({u})"
lines = list(FAM['lines']) + ['General']
for g in lines:
    hs = [h for h in INV['hallazgos'] if (h.get('linea') or 'General') == g]
    if not hs: continue
    out.append(f'### {"Historia y apellido" if g == "General" else "Línea " + g}\n')
    for h in hs:
        x = X[h['id']]
        who = P[x['p']]['name'] if x.get('p') in P else ''
        head = f"**{h['id']} · {h['clasificacion']}** · {h['titulo']}" + (f" — *{who}*" if who else '')
        out.append(f"- {head}" + (' · **aplicado al árbol**' if x.get('a') else ''))
        if h.get('original') or h.get('nuevo'):
            out.append(f"  - Original: {h.get('original') or '—'} → {'ahora' if x.get('a') else 'propuesta'}: {h.get('nuevo') or '—'}")
        out.append(f"  - {h['texto']}")
        out.append(f"  - Fuentes: " + '; '.join(src(k) for k in h['fuentes']))
    out.append('')
out.append('## 7. Todas las fuentes\n')
for k, f in F.items():
    out.append(f"- `{k}` — {src(k)} ({f['tipo']})")
open(os.path.join(R, 'investigacion/HALLAZGOS.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print('HALLAZGOS.md:', len(INV['hallazgos']), 'hallazgos,', len(F), 'fuentes')
