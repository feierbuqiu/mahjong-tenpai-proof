
import json
HON = {"E": 27, "S": 28, "W": 29, "N": 30, "Haku": 31, "Hatsu": 32, "Chun": 33}
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def name2idx(nm):
    nm = str(nm).strip()
    if nm in HON: return HON[nm]
    if nm and nm[0] in "mps": return "mps".index(nm[0])*9 + int(nm[1:]) - 1
    return "mps".index(nm[-1])*9 + int(nm[0]) - 1
def to_idx_any(x):
    if isinstance(x, int): return x
    return name2idx(x)
m = json.load(open("work/verify/waste_list_exact.json", encoding="utf-8"))
A = set()
for e in m["waste_by_class"]:
    W = tuple(sorted(to_idx_any(x) for x in e["W"]))
    for c in e["codes"]:
        A.add((W, tuple(sorted(to_idx_any(x) for x in c))))
a = json.load(open("work/lowerbound/waste_list.json", encoding="utf-8"))
B = set()
for e in a["classes"]:
    W = tuple(sorted(to_idx_any(x) for x in e["W"]))
    for c in e["del"]:
        B.add((W, tuple(sorted(to_idx_any(x) for x in c))))
print("mine set:", len(A), " analyst set:", len(B))
onlyA = A - B; onlyB = B - A
print("only mine:", len(onlyA), " only analyst:", len(onlyB))
print("only analyst 样例 (他们删/我保留):")
for x in list(onlyB)[:6]: print("   ", [NM(t) for t in x[0]], "码", [NM(t) for t in x[1]])
print("only mine 样例 (我删/他们保留):")
for x in list(onlyA)[:6]: print("   ", [NM(t) for t in x[0]], "码", [NM(t) for t in x[1]])
