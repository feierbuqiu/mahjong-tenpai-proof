
import json
c = json.load(open("work/lowerbound/k3_disproof_certificate.json", encoding="utf-8"))
bad = []
for s in c["all_class_W"]:
    for x in str(s).split(","):
        x = x.strip()
        if not x: continue
        if not (x[-1] in "mps" or x in ("E","S","W","N","Haku","Hatsu","Chun")): bad.append((s, x))
for e in c["L_classes"]:
    for x in e["W"]:
        if not (x[-1] in "mps" or x in ("E","S","W","N","Haku","Hatsu","Chun")): bad.append((e["W"], x))
print("bad entries:", len(bad), bad[:5])
print("sample all_class_W:", c["all_class_W"][:3])
print("any with odd chars:", [s for s in c["all_class_W"] if any(ch not in "0123456789mpsz," for ch in s)][:5])
