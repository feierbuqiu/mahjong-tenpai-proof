
import sys, json, collections
sys.path.insert(0,"work/verify")
import indep_core as IC
HONI={"E":27,"S":28,"W":29,"N":30,"Haku":31,"Hatsu":32,"Chun":33}
HON=["E","S","W","N","Haku","Hatsu","Chun"]
def nm(t): return ("%d%s"%(t%9+1,"mps"[t//9])) if t<27 else HON[t-27]
def ti(x):
    if isinstance(x,int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9+int(x[0])-1
B=json.load(open("work/verify/block_coverage_exact.json",encoding="utf-8"))
bad=B["uncovered_I"]+B["uncovered_II"]
print("未覆盖基式条目:",len(bad)," 涉及类:",len(set(tuple(x["W"]) for x in bad)))
ok=0; mis=[]; rows=[]
for x in bad:
    W=frozenset(ti(t) for t in x["W"])
    h=[0]*34
    for t in range(34): h[t]=x["witness"].count(nm(t))
    assert sum(h)==13 and max(h)<=4, x["witness"]
    W2=frozenset(IC.compute_W(h))
    same = (W2==W)
    if same: ok+=1
    else: mis.append({"W":x["W"],"witness":x["witness"],"W_computed":[nm(t) for t in sorted(W2)]})
    rows.append({"W":x["W"],"kind":x["kind"],"witness":x["witness"],"class_ok":same})
print("见证手牌 W 复算与类一致:",ok,"/",len(bad)," 不一致:",len(mis))
for m in mis[:6]: print("   不一致:",m)
out={"plan":"work/recon/plan_k4_leadC.json",
     "sha256":"b1d38ca0aad8aead8830ae39b4876b4d91e4ffbbc620c17a6ace67e7a9ad8fa2",
     "n_uncovered_bases":len(bad),"n_uncovered_I":B["I_uncovered"],"n_uncovered_II":B["II_uncovered"],
     "classes":sorted(set(tuple(x["W"]) for x in bad)),
     "witness_class_check":{"verified":ok,"mismatch":len(mis),"mismatch_examples":mis[:5]},
     "items":rows}
json.dump(out, open("work/verify/leadC_remaining.json","w",encoding="utf-8"), ensure_ascii=False, indent=1)
print("类清单:",[",".join(x) for x in out["classes"]])
