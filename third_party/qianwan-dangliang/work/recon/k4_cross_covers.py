
import json, itertools, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
p=json.load(open(r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"))
empty=[x for x in p["plan"] if not x.get("codes")]
HONOR={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
def s2t(s):
    if s in HONOR: return HONOR[s]
    if s.endswith("z"): return 27+int(s[:-1])-1
    return (0 if s.endswith("m") else 1 if s.endswith("p") else 2)*9+int(s[:-1])-1
def wkey(w):
    if w and isinstance(w[0],str): return frozenset(s2t(x) for x in w)
    return frozenset(w)
emptymasks={wkey(x["W"]) for x in empty}
LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def catlen(c): return 9 if c<3 else 7
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
def min_blocks(uni):
    bs=sorted(set(uni), key=sum); keep=[]
    for v in bs:
        if not any(all(a<=b for a,b in zip(k,v)) for k in keep): keep.append(v)
    return keep
out={}
for c in d["classes"]:
    if frozenset(s2t(x) for x in c["W"]) not in emptymasks: continue
    uni=[]
    for s in c["sources"]:
        if s.get("kind")=="I":
            A=parse_A(s["A"], LETTER.index(s["cat"]))
            if sum(A)>=4: uni.append(A)
        elif s.get("kind")=="II":
            A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
            A=tuple(a+b for a,b in zip(A1,A2))
            if sum(A)>=4: uni.append(A)
    blocks=min_blocks(uni)
    tiles=[t for bi,b in enumerate(blocks) for t,n in enumerate(b) if n]
    tiles=sorted(set(tiles))
    if not blocks:
        out[str(frozenset(s2t(x) for x in c["W"]))]={"W":c["W"],"codes":[],"blocks":0,"uncovered":0}; continue
    pats=[tuple(sorted(q)) for q in itertools.combinations_with_replacement(tiles,4)]
    cov=[]
    for q in pats:
        m=0
        for bi,A in enumerate(blocks):
            ok=True
            for t in set(q):
                if A[t]<q.count(t): ok=False; break
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
    out[str(frozenset(s2t(x) for x in c["W"]))]={"W":c["W"],"codes":chosen,"blocks":len(blocks),"uncovered":bin(unc).count("1")}
    if bin(unc).count("1"): print("UNCOVERED", c["W"], "blocks",len(blocks),"left",bin(unc).count("1"), flush=True)
print("computed covers for", len(out), "classes; Σcodes", sum(len(v["codes"]) for v in out.values()), flush=True)
print("with uncovered:", sum(1 for v in out.values() if v["uncovered"]))
json.dump(out, open(r"D:\DSH\MJ2\work\recon\k4_cross_covers.json","w"))
print("written k4_cross_covers.json")