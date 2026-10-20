import sys, os, json
sys.path.insert(0,'D:/DSH/MJ2/work/audit')
import importlib.util
spec=importlib.util.spec_from_file_location("t12","D:/DSH/MJ2/work/audit/t12_hard_bases.py")
# avoid running main: read hard bases and reproduce config logic
from mjcore import from_str, nm, nm_idx
hard=json.load(open('D:/DSH/MJ2/work/audit/t6_hard_bases.json'))
print("n hard", len(hard))
for i,b in enumerate(hard):
    A=b["A"]
    Av=from_str(A)
    s=sum(Av)
    if b["kind"]=="I":
        inert=tuple(x for x in range(4) if x!=b["c"])
    else:
        inert=tuple(x for x in range(4) if x not in (b["c1"],b["c2"]))
    m=13-s
    if m<0 or m>12*len(inert) or m%3:
        print("PROBLEM at",i,b,"sum A=",s,"m=",m,"inert",inert)
        if i>5: break
print("sample entries:")
for b in hard[:3]: print("  ", b)
print("kinds:", set(b["kind"] for b in hard))
print("modes:", set(b.get("mode") for b in hard))
