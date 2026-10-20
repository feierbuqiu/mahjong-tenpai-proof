
import json
from collections import Counter
mine = set(frozenset(x) for x in json.load(open("work/verify/census_strict.json", encoding="utf-8")))
d = json.load(open("work/data/out/global.json", encoding="utf-8"))
theirs = set()
for row in d["classes"]:
    W = row.get("W")
    if W is None: print("no W key:", list(row.keys())); break
    theirs.add(frozenset(W))
print("mine", len(mine), "theirs", len(theirs))
print("theirs - mine:", len(theirs - mine))
print("mine - theirs:", len(mine - theirs))
print("theirs<=mine ?", theirs <= mine)
om = sorted([sorted(x) for x in (mine - theirs)], key=len)
print("size dist of mine-theirs:", dict(sorted(Counter(len(x) for x in (mine-theirs)).items())))
print("first 15 extra:", om[:15])
print("their no_common_code:", d.get("no_common_code"), "sum_K:", d.get("sum_K_over_classes"))
print("their counts:", json.dumps(d.get("counts"), ensure_ascii=False)[:500])
# 检查 extra 是否都能在"单类别"结构里找到 (快速): 只看 W 是否落在单一类别
def cats(W):
    s=set()
    for t in W:
        s.add(0 if t<9 else 1 if t<18 else 2 if t<27 else 3)
    return s
print("extra cat-count dist:", dict(sorted(Counter(len(cats(x)) for x in (mine-theirs)).items())))
print("their cat-count dist:", dict(sorted(Counter(len(cats(x)) for x in theirs).items())))
