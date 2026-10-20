
import json, itertools, math, time
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def catlen(c): return 9 if c<3 else 7
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[t//9])) if t<27 else ("%dz"%((t-27)+1))
t0=time.time()
out={}
for c in CLS:
    sub=c["sub_universe"]
    if not sub: continue
    letter=sub[0]; cat=LETTER.index(letter)
    blocks=[]
    for s in c["sources"]:
        if s.get("kind")=="I" and s["cat"]==letter:
            A=parse_A(s["A"],cat)
            if sum(A)>=4: blocks.append(A)
        elif s.get("kind")=="II" and letter in s["cats"]:
            j=s["cats"].index(letter)
            A=parse_A(s["minA1"] if j==0 else s["minA2"],cat)
            if sum(A)>=4: blocks.append(A)
    blocks=list(set(blocks))
    if not blocks:
        out[str(c["Wmask"])]={"W":c["W"],"letter":letter,"codes":[],"blocks":0,"uncovered":0}; continue
    tiles=[base_of(cat)+i for i in range(catlen(cat))]
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
    unc=(1<<len(blocks))-1; chosen=[]
    while unc:
        best=-1; bc=0
        for pi,m in enumerate(cov):
            n=bin(m&unc).count("1")
            if n>bc: bc=n; best=pi
        if best<0 or bc==0: break
        chosen.append(list(pats[best])); unc &= ~cov[best]
    out[str(c["Wmask"])]={"W":c["W"],"letter":letter,"codes":chosen,"blocks":len(blocks),"uncovered":bin(unc).count("1")}
    if bin(unc).count("1"): print("UNCOVERED", c["W"], bin(unc).count("1"), flush=True)
tot=sum(len(v["codes"]) for v in out.values())
print("classes covered:", len(out), "Σcodes:", tot, "time %.1fs"%(time.time()-t0), flush=True)
json.dump(out, open(r"D:\DSH\MJ2\work\recon\k4_subuniverse_covers.json","w"))
print("written")
