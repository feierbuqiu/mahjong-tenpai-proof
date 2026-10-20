import json, sys
sys.stdout.reconfigure(encoding="utf-8")
A=json.load(open("work/lowerbound/waste_list.json",encoding="utf-8"))
S=set()
for cl in A["classes"]:
    for c in cl["del"]: S.add((tuple(sorted(c)), tuple(sorted(cl["W"]))))
print("我的精确清单: %d 条, %d 类" % (len(S), len(A["classes"])))
# 与 verifier 例子对拍
EX=[(["1m","3p","3p","6p"],["1m"]),(["1m","7p","7p","4s"],["1m"]),(["1m","8p","8p","1s"],["1m"]),
    (["1m","N","N","Chun"],["1m"]),(["1m","1m","N","2m"],["1m","2m","3m"])]
for c,W in EX:
    print("verifier 例子 code=%s class=%s 在我的精确清单里? %s" % (c, W, (tuple(sorted(c)),tuple(sorted(W))) in S))
