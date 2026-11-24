import sys,json,re
sys.path.insert(0,sys.argv[0].rsplit('/',1)[0])
from parse import load,lines_of,strip_header
sys.stdout.reconfigure(encoding='utf-8')
YT={'Y','E'}
def kind(w):
    t=w['t']
    if t in ('|','XXX','XX','I','l'): return 'C'
    if t in ('v','V','.','-','–','B','B.','(',')'): return 'IGN'
    if t in YT: return 'Y'
    return 'T'
def fix_wraps(lines):
    # short lines hugging the left margin between bigger lines = wrapped tail of previous line
    out=[]
    for i,l in enumerate(lines):
        if out and len(l)<=3 and max(w['x'] for w in l)<45 and len(out[-1])>=6 and min(w['x'] for w in out[-1])>60:
            # leftmost of prev line is to the right; ambiguous; keep as is
            pass
        if out and len(l)<=3 and max(w['x'] for w in l)<45 and len(out[-1])>=6:
            prev=out[-1]; mx=max(w['x'] for w in prev)
            for w in l:
                w=dict(w); w['x']=mx+25+ (w['x']-l[0]['x']); w['wrap']=True; prev.append(w)
            continue
        out.append(list(l))
    return out
def parse_page(pdf,pno,tree):
    lines=fix_wraps(strip_header(lines_of(load(pdf,pno))))
    bands=[];cur=None;pendingY=[]
    for l in lines:
        ks=[kind(w) for w in l]
        hasT=any(k=='T' for k in ks); hasY=any(k=='Y' for k in ks)
        numline = sum(re.fullmatch(r'\d{1,2}',w['t']) is not None for w in l)>3 and all(re.fullmatch(r'\d{1,2}|XXX|v|V',w['t']) for w in l)
        if numline:
            for w in l: cur['refs'].append(w)
            continue
        onlyCY = not hasT and hasY
        if (hasT and hasY) or cur is None:
            cur=dict(text=[],anchors=[],ys=list(pendingY),refs=[],lines=[]); bands.append(cur); pendingY=[]
        for w,k in zip(l,ks):
            if k=='C': cur['anchors'].append(w)
            elif k=='Y':
                if onlyCY: pendingY.append(w)
                else: cur['ys'].append(w)
            elif k=='T': cur['text'].append(w)
    return bands
if __name__=='__main__':
    pdf=sys.argv[1]
    for pno in map(int,sys.argv[2].split(',')):
        bands=parse_page(pdf,pno,0)
        print('PAGE',pno)
        for i,b in enumerate(bands):
            an=sorted(b['anchors'],key=lambda w:w['x'])
            print(f" band{i}: anchors={len(an)} (| {sum(a['t']=='|' for a in an)}) Y={len(b['ys'])} refs={len(b['refs'])} text={len(b['text'])}")
