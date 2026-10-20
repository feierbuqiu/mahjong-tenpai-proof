
import json, itertools, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
CLS=d["classes"]; LETTER="mpsz"
def cat_of(t): return t//9 if t<27 else 3
def base_of(c): return c*9 if c<3 else 27
def parse_A(s,cat):
    base=base_of(cat); v=[0]*34
    for i,ch in enumerate(s):
        n=int(ch)
        if n: v[base+i]=n
    return tuple(v)
def t2s(t): return ("%d%s"%((t%9)+1,LETTER[cat_of(t)])) if t<27 else ("%dz"%((t-27)+1))
def perms(p): return list(set(itertools.permutations(p)))
def sparse(v): return "".join("%s:%d"%(t2s(t),n) for t,n in enumerate(v) if n)
for c in CLS:
    if c["W"]==['1m','3m','4m','5m','6m']:
        blocks=[]
        for s in c["sources"]:
            if s.get("kind")=="I": blocks.append(parse_A(s["A"], LETTER.index(s["cat"])))
            elif s.get("kind")=="II":
                A1=parse_A(s["minA1"], LETTER.index(s["cats"][0])); A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
                blocks.append(tuple(a+b for a,b in zip(A1,A2)))
        blocks=list(set(blocks))
        print("blocks:", [sparse(b) for b in blocks[:6]], "n=",len(blocks))
        tiles=[t for t,n in enumerate(blocks[0]) if n]
        univ=list(itertools.combinations_with_replacement(tiles,3))
        print("univ size:", len(univ), "| one block A: ", sparse(blocks[0]))
        for bi,A in enumerate(blocks[:3]):
            cands=[p for p in univ if all(A[t]>=p.count(t) for t in set(p))]
            print(" block",bi,"#patterns:",len(cands), cands[:5])
        break
