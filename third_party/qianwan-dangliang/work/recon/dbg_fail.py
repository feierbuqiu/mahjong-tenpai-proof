
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
def sparse(v): return "".join("%s:%d"%(t2s(t),n) for t,n in enumerate(v) if n)
target=['1m','3m','4m','5m','6m']
for c in CLS:
    if c["W"]==target:
        print("class", c["W"], "Wmask", c["Wmask"], "sub", c["sub_universe"], "n_sources", len(c["sources"]))
        sizes=collections.Counter()
        for s in c["sources"]:
            if s.get("kind")=="I":
                A=parse_A(s["A"], LETTER.index(s["cat"])); sizes[("I",sum(A))]+=1
                if sum(A)<3: print("   small I:", sparse(A), s)
            elif s.get("kind")=="II":
                A1=parse_A(s["minA1"], LETTER.index(s["cats"][0]))
                A2=parse_A(s["minA2"], LETTER.index(s["cats"][1]))
                A=tuple(a+b for a,b in zip(A1,A2)); sizes[("II",sum(A))]+=1
                if sum(A)<3: print("   small II:", sparse(A), json.dumps(s,ensure_ascii=False)[:200])
        print("   size histogram:", dict(sorted(sizes.items())))
        break
