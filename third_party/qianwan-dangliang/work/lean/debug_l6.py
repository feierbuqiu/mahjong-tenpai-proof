# -*- coding: utf-8 -*-
"""work/lean/debug_l6.py -- 调查中间批次的大量"失败"是真缺陷还是脚本 bug。"""
import sys, os, json, pickle, re
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "work", "strategy")); sys.path.insert(0, os.path.join(ROOT, "work", "strategy", "out"))
import table_lib as TL
exec(open(os.path.join(HERE, "verify_l6.py"), encoding="utf-8").read().split('if __name__ == "__main__"')[0])
init(None)
combos, recs, PII, grp, order, plan = _G["combos"], _G["recs"], _G["PII"], _G["grp"], _G["order"], _G["plan"]
BASE_ = [0, 9, 18, 27]

def blockinfo(rec):
    classIdx = rec >> 25; r1 = rec & ((1 << 25) - 1); comboIdx = r1 >> 18
    r2 = r1 & ((1 << 18) - 1); k1i = r2 >> 9; k2i = r2 & 511
    c1, s1, c2, s2 = combos[comboIdx]
    W = order[classIdx]
    codes = [c for c in plan[W] if all((0 if t < 27 else 3) in (c1, c2) for t in c)]
    xs1 = PII[(c1, s1, grp[(c1, s1)][k1i])][1]
    xs2 = PII[(c2, s2, grp[(c2, s2)][k2i])][1]
    return classIdx, (c1, s1, k1i, c2, s2, k2i), W, codes, xs1, xs2

# 在 20000..40000 找第一个失败块
found = 0
for rec in recs[20000:40000]:
    classIdx, key, W, codes, xs1, xs2 = blockinfo(rec)
    m = 13 - key[1] - key[4]
    inert = tuple(i for i in range(4) if i not in (key[0], key[3]))
    bad_unit = None
    for X1 in xs1:
        for X2 in xs2:
            A = [0]*34
            for i,v in enumerate(X1): A[BASE_[key[0]]+i]+=v
            for i,v in enumerate(X2): A[BASE_[key[3]]+i]+=v
            if not any(contains(A,c) for c in codes):
                if not dfs_block(codes, A, inert, m):
                    bad_unit = (X1, X2, A); break
        if bad_unit: break
    if bad_unit:
        found += 1
        print("FAILING BLOCK rec=%d classIdx=%d key=%s W=%s" % (rec, classIdx, key, sorted(W)))
        print("  #codes inside c1/c2:", len(codes), " total codes of class:", len(plan[W]))
        print("  #xs1=%d #xs2=%d m=%d inert=%s" % (len(xs1), len(xs2), m, inert))
        X1, X2, A = bad_unit
        print("  failing X1=%s X2=%s" % (X1, X2))
        print("  codes(sample):", codes[:6])
        # 手工找见证 F
        wit = None
        def rec2(i, left, h, path):
            global wit
            for c in codes:
                if contains(h, c): return True
            if i == len(inert):
                if left == 0:
                    wit = (list(h), list(path)); return False
                return True
            ci = inert[i]
            for s in range(0, left+1, 3):
                for v in _G["dec"][ci].get(s, ()):
                    h2 = list(h); p2 = list(path)
                    for t,x in enumerate(v): h2[BASE_[ci]+t]+=x
                    p2.append((ci, v))
                    if not rec2(i+1, left-s, h2, p2): return False
            return True
        ok = rec2(0, m, A, [])
        print("  witness found:", (not ok), " F =", wit[1] if wit else None)
        if wit:
            F = wit[0]
            # 验证 F 合法性：每门是面子并集、总张数 m
            tot = 0
            for ci, v in wit[1]:
                tot += sum(v)
                # 检查 v 属于该门面子并集
                s = sum(v)
                print("    cat", ci, "vec", v, "in filler table:", tuple(v) in set(_G["dec"][ci].get(s, ())))
            print("    F total =", tot, " expected m =", m)
            print("    no code ⊆ A+F :", not any(contains(F, c) for c in codes))
        break
print("done, failing blocks scanned:", found)
