
import json, itertools, math, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
def nperm(p):
    f=1
    for x in set(p): f*=math.factorial(p.count(x))
    return 24//f
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[t//9])) if t<27 else ("%dz"%((t-27)+1))
targets=[['1m','4m','7m'],['3m','6m','9m'],['2m','5m','8m'],['1p','4p','7p'],['3p','6p','9p'],['2p','5p','8p'],['1s','4s','7s'],['3s','6s','9s'],['2s','5s','8s']]
out={}
for c in CLS:
    if c["W"] not in targets: continue
    blocks=[]
    for s in c["sources"]:
        if s.get("kind")=="I":
            A=parse_A(s["A"], LETTER.index(s["cat"]))
            if sum(A)>=4: blocks.append(A)
        elif s.get("kind")=="II":
            A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
            A=tuple(a+b for a,b in zip(A1,A2))
            if sum(A)>=4: blocks.append(A)
    blocks=list(set(blocks))
    cat=0 if c["W"][0].endswith("m") else (1 if c["W"][0].endswith("p") else 2)
    tiles=[base_of(cat)+i for i in range(9)]
    pats=[tuple(sorted(p)) for p in itertools.combinations_with_replacement(tiles,4)]
    cov=[]
    for p in pats:
        m=0
        for bi,A in enumerate(blocks):
            ok=True
            for t in set(p):
                if A[t]<p.count(t): ok=False; break
            if ok: m|=1<<bi
        cov.append(m)
    unc=(1<<len(blocks))-1; chosen=0
    while unc:
        best=-1; bc=0
        for pi,m in enumerate(cov):
            c2=bin(m&unc).count("1")
            if c2>bc: bc=c2; best=pi
        if best<0 or bc==0: break
        chosen+=1; unc &= ~cov[best]
    out[str(c["W"])]=dict(blocks=len(blocks), cover_codes=chosen, uncovered=bin(unc).count("1"))
    print(c["W"], "blocks",len(blocks), "k=4 greedy cover =", chosen, "uncovered", bin(unc).count("1"), flush=True)
json.dump(out, open(r"D:\DSH\MJ2\work\recon\k4_nine_covers.json","w"))
