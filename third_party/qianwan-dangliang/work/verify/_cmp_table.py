
import pickle, json
from collections import Counter
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
d = pickle.load(open("work/strategy/out/table.pkl", "rb"))
cls = d["cls"]
theirs = set(cls.keys())
print("mine", len(mine), "table", len(theirs))
print("table - mine:", len(theirs - mine), " mine - table:", len(mine - theirs))
em = theirs - mine
print("extra size dist:", dict(sorted(Counter(len(W) for W in em).items())))
ex = sorted([sorted(x) for x in em], key=lambda x: (len(x), x))
print("extras:", ex[:40])
