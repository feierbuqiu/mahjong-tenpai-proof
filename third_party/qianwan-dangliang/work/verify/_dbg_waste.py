
import json, sys, pickle, os
sys.path.insert(0, "work/verify"); sys.path.insert(0, "work/strategy")
from waste_exact import PROFI_D, PROFII_D, CLS, absorb, active_ok, active_vec, to_idx_one, dec_vecs, CAT_BASE, CAT_LEN
# 从 audit 例子里取第一条
d = json.load(open("work/verify/waste_list_exact.json", encoding="utf-8"))
ex = d["audit"]["examples"]
print("audit 误报样例数:", len(ex), " 误报总数:", d["audit"]["false_positives"], "/", d["audit"]["sampled"])
if ex:
    e = ex[0]
    W = frozenset(to_idx_one(x) for x in e["W"]); c = [to_idx_one(x) for x in e["code"]]
    cv = [0]*34
    for t in c: cv[t] += 1
    print("类", e["W"], "码", e["code"], "见证手牌", sum(e["hand"]), "张")
    print("该类 blocks 数:", len(CLS.get(W, [])))
    for b in CLS.get(W, [])[:12]:
        kind = b[0]
        if kind == "I":
            key = b[1]
            a = active_ok(key, active_vec(key, cv, key[0]))
            inert = tuple(i for i in range(4) if i != key[0])
            dd = list(cv)
            for i in range(CAT_BASE[key[0]], CAT_BASE[key[0]]+CAT_LEN[key[0]]): dd[i]=0
            ab = absorb(inert, 13-key[1], dd)
            print("  I", key, "active_ok", a, "absorb", ab, "inert", inert)
        elif kind == "II":
            k1, k2 = b[1], b[2]
            a1 = active_ok(k1, active_vec(k1, cv, k1[0])); a2 = active_ok(k2, active_vec(k2, cv, k2[0]))
            inert = tuple(i for i in range(4) if i not in (k1[0], k2[0]))
            dd = list(cv)
            for i in list(range(CAT_BASE[k1[0]], CAT_BASE[k1[0]]+CAT_LEN[k1[0]]))+list(range(CAT_BASE[k2[0]], CAT_BASE[k2[0]]+CAT_LEN[k2[0]])): dd[i]=0
            ab = absorb(inert, 13-k1[1]-k2[1], dd)
            print("  II", k1, k2, "active", a1, a2, "absorb", ab, "inert", inert)
        else:
            print("  other kind", kind)
