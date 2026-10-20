
import json
m = json.load(open("work/verify/waste_list_exact.json", encoding="utf-8"))
A = set()
for e in m["waste_by_class"]:
    W = tuple(sorted(e["W"]))
    for c in e["codes"]:
        A.add((W, tuple(sorted(c))))
a = json.load(open("work/lowerbound/waste_list.json", encoding="utf-8"))
B = set()
for e in a["classes"]:
    W = tuple(sorted(e["W"]))
    for c in e["del"]:
        B.add((W, tuple(sorted(c))))
print("mine set:", len(A), "(raw count", m["waste_count"], ")  analyst set:", len(B), "(raw total", a["total"], ")")
onlyA = A - B; onlyB = B - A
print("only mine:", len(onlyA), " only analyst:", len(onlyB))
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONN[t-27]
def show(x):
    W, c = x
    return ([NM(t) for t in W], [NM(t) for t in c])
print("only analyst 样例 (他们删、我认为可用 => 风险):")
for x in list(onlyB)[:8]:
    print("   ", [NM(t) for t in x[0]], "码", [NM(t) for t in x[1]])
print("only mine 样例 (我删、他们保留):")
for x in list(onlyA)[:6]:
    print("   ", [NM(t) for t in x[0]], "码", [NM(t) for t in x[1]])
