import fitz,sys,json,re
sys.stdout.reconfigure(encoding='utf-8')
CONN={'|','XXX','v','V','I','l'}
def is_conn_line(ws):
    toks=[w['t'] for w in ws]
    if all(t in CONN or t in '.-' for t in toks) and any(t in ('|','XXX') for t in toks): return True
    if all(re.fullmatch(r'\d{1,2}|XXX|V|v|\.',t) for t in toks) and sum(t.isdigit() for t in toks)>3: return True  # tree1 numbers
    return False
def load(pdf,pno):
    d=fitz.open(pdf); p=d[pno-1]
    dic=p.get_text("dict")
    spans=[s for b in dic['blocks'] for l in b.get('lines',[]) for s in l['spans']]
    out=[]
    for w in p.get_text("words"):
        cx=(w[0]+w[2])/2; cy=(w[1]+w[3])/2; sz=10; col=0
        for s in spans:
            x0,y0,x1,y1=s['bbox']
            if x0-.5<=cx<=x1+.5 and y0-.5<=cy<=y1+.5 and s['text'].strip(): sz=s['size']; col=s['color']; break
        out.append(dict(t=w[4],x0=w[0],x1=w[2],x=cx,y=cy,sz=sz,c='#%06x'%col))
    return out
def lines_of(words):
    words=sorted(words,key=lambda w:w['y'])
    L=[]
    for w in words:
        if L and abs(L[-1][-1]['y']-w['y'])<=0.3*min(w['sz'],L[-1][-1]['sz']) + 0.5:
            L[-1].append(w)
        else: L.append([w])
    return [sorted(l,key=lambda w:w['x']) for l in L]
def strip_header(lines):
    out=[];skip=False
    for i,l in enumerate(lines):
        txt=' '.join(w['t'] for w in l)
        if 'ASCEND' in txt or txt.startswith('#') or re.fullmatch(r'(TOTAL )?\d{3,4}',txt) and l[0]['sz']>=11.5 and i>0 and ('ASCEND' in ' '.join(w['t'] for w in lines[i-1])):
            continue
        out.append(l)
    return out
if __name__=='__main__':
    ws=load(sys.argv[1],int(sys.argv[2]))
    for l in strip_header(lines_of(ws)):
        print(('C ' if is_conn_line(l) else '  ')+f"{l[0]['y']:.0f} "+'  '.join(f"{w['t']}@{w['x']:.0f}" for w in l)[:400])
