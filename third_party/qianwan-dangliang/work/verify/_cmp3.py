
import json
from collections import Counter
SUITS = {'m':0,'p':9,'s':18}
HON = {'E':27,'S':28,'W':29,'N':30,'Haku':31,'Hatsu':32,'Chun':33}
def to_idx(name):
    if name in HON: return HON[name]
    return SUITS[name[-1]] + int(name[0]) - 1
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
d = json.load(open("work/data/out/global.json", encoding="utf-8"))
theirs = set(frozenset(to_idx(n) for n in r["W"]) for r in d["classes"])
print("mine", len(mine), "theirs", len(theirs))
print("theirs - mine:", len(theirs - mine), " mine - theirs:", len(mine - theirs))
print("theirs<=mine:", theirs <= mine)
em = mine - theirs
print("mine-theirs size dist:", dict(sorted(Counter(len(x) for x in em).items())))
ex = sorted([sorted(x) for x in em], key=lambda x: (len(x), x))[:20]
print("first extra:", ex)
# 对每个 extra, 判断是否落在单一类别
def ncat(W): return len(set(0 if t<9 else 1 if t<18 else 2 if t<27 else 3 for t in W))
print("extra ncat dist:", dict(sorted(Counter(ncat(x) for x in em).items())))
print("theirs ncat dist:", dict(sorted(Counter(ncat(x) for x in theirs).items())))
