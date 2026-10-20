
import json,collections
g=json.load(open("work/data/out/global.json",encoding="utf-8"))
print("top:",list(g.keys()))
kinds=collections.Counter()
exI=None; exII=None
for row in g["classes"]:
    for s in row.get("sources",[]):
        kinds[s["kind"]]+=1
        if s["kind"]=="I" and exI is None: exI=(row["W"],s)
        if s["kind"]=="II" and exII is None: exII=(row["W"],s)
print("source kind counts:",kinds)
print("I example:",exI)
print("II example:",exII)
