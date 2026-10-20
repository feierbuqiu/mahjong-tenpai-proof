
import json, itertools, collections
P1=r"D:\DSH\MJ2\work\strategy\out\plan_k4.json"     # designer 18:02
P2=r"D:\DSH\MJ2\work\recon\plan_k4_v7.json"          # lead v8 输出(文件名沿用)
d=json.load(open(P1)); mine=json.load(open(P2))
plan=d["plan"] if isinstance(d,dict) else d
def keyof(e):
    w=e["W"]
    if w and isinstance(w[0],str): return frozenset(w)
    L="mpsz"
    def t2s(t): return ("%d%s"%((t%9)+1,L[t//9])) if t<27 else ("%dz"%((t-27)+1))
    return frozenset(t2s(t) for t in w)
mineby={keyof(e):[tuple(c) for c in e["codes"]] for e in mine["plan"]}
used=set(); out=[]; added=0; skipped=0; empt=0
for e in plan:
    codes=[]
    for c in e.get("codes",[]):
        c=tuple(c)
        if c in used:
            for p in sorted(set(itertools.permutations(c))):
                if p not in used: c=p; break
        if c not in used: used.add(c); codes.append(c)
    if not codes:
        k=keyof(e)
        for pat in mineby.get(k,[]):
            pat=tuple(sorted(pat))
            if len(pat)!=4: skipped+=1; continue
            for p in sorted(set(itertools.permutations(pat))):
                if p not in used: used.add(p); codes.append(p); added+=1; break
            else: skipped+=1
    if not codes: empt+=1
    out.append({"W":e["W"],"codes":[list(c) for c in codes]})
allc=[tuple(c) for e in out for c in e["codes"]]
print("classes:",len(out),"codes:",len(allc),"distinct:",len(set(allc)),"dups:",len(allc)-len(set(allc)),
      "added_from_v8:",added,"skipped:",skipped,"empty:",empt)
json.dump({"k":4,"n_classes":len(out),"n_codes":len(set(allc)),"plan":out},
          open(r"D:\DSH\MJ2\work\recon\plan_k4_u1.json","w"))
print("written plan_k4_u1.json")
