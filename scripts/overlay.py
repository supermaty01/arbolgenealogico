import sys, json, fitz
from PIL import Image, ImageDraw, ImageFont
pdf, tj, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
trees = json.load(open(tj, encoding='utf-8'))
only = set(sys.argv[4].split(',')) if len(sys.argv) > 4 else None
d = fitz.open(pdf); Z = 2.0
font = ImageFont.truetype('arial.ttf', 13)
COLS = ['#e6194b', '#3cb44b', '#4363d8', '#f58231', '#911eb4', '#008080', '#9a6324', '#800000']
for t, T in trees.items():
    if only and t not in only: continue
    pages = sorted(set(p['page'] for p in T['people'] if p['page']))
    imgs = {}
    for pg in pages:
        pix = d[pg - 1].get_pixmap(matrix=fitz.Matrix(Z, Z))
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        im = Image.blend(im, Image.new('RGB', im.size, 'white'), 0.45)
        imgs[pg] = im
    by = {p['id']: p for p in T['people']}
    for p in T['people']:
        if not p['bbox']: continue
        dr = ImageDraw.Draw(imgs[p['page']])
        c = COLS[p['band'] % len(COLS)]
        x0, y0, x1, y1 = [v * Z for v in p['bbox']]
        dr.rectangle([x0, y0, x1, y1], outline=c, width=2)
        if p['father']:
            f, m = by[p['father']], by[p['mother']]
            if f['bbox'] and m['bbox']:
                cx = (x0 + x1) / 2
                tx = (f['bbox'][2] + m['bbox'][0]) / 2 * Z
                ty = min(f['bbox'][1], m['bbox'][1]) * Z
                if f['page'] == p['page']:
                    dr.line([cx, y1, tx, ty], fill=c, width=3)
                    dr.line([f['bbox'][2] * Z, ty, m['bbox'][0] * Z, ty], fill=c, width=1)
        if p['none']: dr.text((x0, y1 + 1), 'Ø', fill='black', font=font)
    for pg, im in imgs.items():
        # crop to content
        ys = [p['bbox'][1] * Z for p in T['people'] if p['page'] == pg and p['bbox']] + [p['bbox'][3] * Z for p in T['people'] if p['page'] == pg and p['bbox']]
        im = im.crop((0, max(0, min(ys) - 20), im.width, min(im.height, max(ys) + 20)))
        im.save(f'{outdir}/ov_T{int(t):02d}_p{pg}.png')
        print(t, pg, im.size)
