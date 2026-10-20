
import json
HONn = ["E","S","W","N","Haku","Hatsu","Chun"]
NM = lambda t: ("%d%s" % (t%9+1, "mps"[t//9])) if t < 27 else HONn[t-27]
d = json.load(open("work/verify/k4_gap_classes.json", encoding="utf-8"))
print("zero-code classes:", [[NM(t) for t in W] for W in d["zero_code_classes"]])
for s in ("m","p","s"):
    print(s, "classes_with_failures", d["suits"][s]["classes_with_failures"], "uncovered", d["suits"][s]["uncovered_hands_total"])
