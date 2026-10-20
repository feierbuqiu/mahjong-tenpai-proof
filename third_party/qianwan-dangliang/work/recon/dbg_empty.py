
import json, itertools, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; LETTER="mpsz"
def base_of(c): return c*9 if c<3 else 27
def cat_of(t): return t//9 if t<27 else 3
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[t//9])) if t<27 else ("%dz"%((t-27)+1))
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
def sparse(v): return "".join("%s:%d"%(t2s(t),n) for t,n in enumerate(v) if n)
def min_blocks(uni):
    bs=sorted(set(uni), key=sum); keep=[]
    for v in bs:
        if not any(all(a<=b for a,b in zip(k,v)) for k in keep): keep.append(v)
    return keep
for c in CLS:
    if c["W"]==['3s','4s','5s','9s']:
        uni=[]; kinds=collections.Counter(); small=[]
        for s in c["sources"]:
            if s.get("kind")=="I":
                A=parse_A(s["A"], LETTER.index(s["cat"])); kinds[("I",sum(A))]+=1
                if sum(A)>=3: uni.append(A)
                else: small.append(("I",sparse(A)))
            elif s.get("kind")=="II":
                A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
                A=tuple(a+b for a,b in zip(A1,A2)); kinds[("II",sum(A))]+=1
                if sum(A)>=3: uni.append(A)
                else: small.append(("II",sparse(A),json.dumps(s,ensure_ascii=False)[:120]))
        mb=min_blocks(uni)
        print("W",c["W"],"sub",c["sub_universe"],"n_src",len(c["sources"]),"kinds",dict(sorted(kinds.items())))
        print("small blocks:", small[:5], "count", len(small))
        print("min blocks:", [(sparse(b),sum(b)) for b in mb[:6]], "n=",len(mb))
        # candidate patterns for the smallest minimal block
        tiles=[t for t,n in enumerate(mb[0]) if n]
        univ=list(itertools.combinations_with_replacement(tiles,3))
        print("smallest block patterns (restricted to its tiles):", len(univ))
        tiles_all=[base_of(2)+i for i in range(9)]
        univ2=list(itertools.combinations_with_replacement(tiles_all,3))
        cands=[p for p in univ2 if all(mb[0][t]>=p.count(t) for t in set(p))]
        print("candidates from full suit universe:", len(cands), cands[:8])
        break
