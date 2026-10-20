# -*- coding: utf-8 -*-
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mjlib import *
import table_lib as TL
T = TL.build(); CLS = T["cls"]
def show(vec): return "".join(tile_name(t)*n for t,n in enumerate(vec))
def vlist(W): return sorted(tile_name(t) for t in W)

def witness_hand(b):
    kind = b[0]
    if kind == "KOK":
        H = [0]*34
        for t in b[1]: H[t] += 1
        return H
    if kind == "I":
        (c, s, pkey) = b[1]; mode = b[3]
        am, xs = T["PROFI_D"][(c, s, pkey)]
        X = xs[0]
        S = tuple(x for x in range(4) if x != c); m = 13-s
        fs = TL.fam_list(S, m, mode == "chi")
        if not fs: return None
        F = fs[0]
        H = [0]*34
        for i in range(CAT_LEN[c]): H[CAT_BASE[c]+i] = X[i]
        for i in range(34): H[i] += F[i]
        return H
    (c1, s1, k1) = b[1]; (c2, s2, k2) = b[2]; mode = b[3]
    am1, xs1 = T["PROFII_D"][(c1, s1, k1)]; am2, xs2 = T["PROFII_D"][(c2, s2, k2)]
    X1 = xs1[0]; X2 = xs2[0]
    S = tuple(x for x in range(4) if x not in (c1, c2)); m = 13-s1-s2
    fs = TL.fam_list(S, m, mode == "chi")
    if not fs: return None
    F = fs[0]
    H = [0]*34
    for i in range(CAT_LEN[c1]): H[CAT_BASE[c1]+i] = X1[i]
    for i in range(CAT_LEN[c2]): H[CAT_BASE[c2]+i] = X2[i]
    for i in range(34): H[i] += F[i]
    return H

targets = [W for W in CLS if len(W) == 12][:2]
targets += [W for W in CLS if len(W) == 3 and not any(
    witness_hand(b) is not None and sum(witness_hand(b)) == 13 and waits13(tuple(witness_hand(b))) == W for b in CLS[W])][:2]
for W in targets:
    print("=== 类 W = %s (%d 块)" % (vlist(W), len(CLS[W])))
    for b in CLS[W][:4]:
        H = witness_hand(b)
        print("  块 %s mode=%s z=%s nsrc=%d" % (b[0], b[3], b[4], b[6]))
        if b[0] == "I":
            (c, s, pkey) = b[1]
            print("     I c=%d s=%d Wp=%s odd=%s ot=%s ps=%s" % (c, s, vlist(pkey[0]), pkey[1], pkey[2], pkey[3]))
        elif b[0] == "II":
            print("     II c1=%d s1=%d k1=%s | c2=%d s2=%d k2=%s" % (b[1][0], b[1][1], b[1][2], b[2][0], b[2][1], b[2][2]))
            V1, pd1, o1, ot1, a21, o21 = b[1][2]; V2, pd2, o2, ot2, a22, o22 = b[2][2]
            print("        V1=%s pd1=%s odd1=%s ot1=%s | V2=%s pd2=%s odd2=%s ot2=%s" % (
                vlist(V1), pd1, o1, ot1, vlist(V2), pd2, o2, ot2))
        if H is None or sum(H) != 13:
            print("    H 无效"); continue
        Wt = waits13(tuple(H))
        print("    H = %s" % show(H))
        print("    W(H) = %s" % vlist(Wt))
