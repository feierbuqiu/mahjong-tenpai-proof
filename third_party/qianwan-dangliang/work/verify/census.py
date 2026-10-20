#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""verifier T5/T6: 独立全局类普查 (签名法), loose/strict 七对子口径 + 字牌不能有顺子.
只用 work/verify/indep_core.py 的面子 DP; 不 import work/data 或 work/strategy.
"""
import sys, os, json, time, itertools, hashlib
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from indep_core import (melds_only, melds_pair, gen_vectors, CAP, KOKUSHI_IDX,
                        melds_only_honor, melds_pair_honor)

class Uni:
    def __init__(self, cat_kinds, cat_is_honor=None, kokushi=False):
        self.cat_kinds = tuple(cat_kinds)
        self.nc = len(self.cat_kinds)
        self.hon = list(cat_is_honor) if cat_is_honor is not None else [False] * self.nc
        self.kokushi = kokushi
        offs = []; s = 0
        for k in self.cat_kinds:
            offs.append(s); s += k
        self.offs = offs; self.nkinds = s
        self.pre = {}
        for ci, K in enumerate(self.cat_kinds):
            key = (K, self.hon[ci])
            if key not in self.pre:
                self.pre[key] = self._pre(K, self.hon[ci])
        self._c1 = {}; self._c2 = {}

    def pre_of(self, c):
        return self.pre[(self.cat_kinds[c], self.hon[c])]

    def g(self, c, local): return self.offs[c] + local
    def cat_of(self, t):
        for c in range(self.nc):
            if t < self.offs[c] + self.cat_kinds[c]: return c
        raise ValueError(t)

    def _mo(self, vec, c):
        return melds_only_honor(vec) if self.hon[c] else melds_only(vec)
    def _mp(self, vec, c):
        return melds_pair_honor(vec) if self.hon[c] else melds_pair(vec)

    def _pre(self, K, is_honor):
        mo = melds_only_honor if is_honor else melds_only
        mp = melds_pair_honor if is_honor else melds_pair
        pre = {}
        for n in range(0, 14):
            vecs = list(gen_vectors(K, n))
            if n % 3 == 1:
                sigs = set()
                for X in vecs:
                    wp = []
                    for t in range(K):
                        if X[t] >= CAP: continue
                        xx = list(X); xx[t] += 1
                        if mp(tuple(xx)): wp.append(t)
                    oddk = tuple(i for i, c in enumerate(X) if c % 2 == 1)
                    sigs.add((frozenset(wp), len(oddk), oddk))
                pre[n] = {'kind': 1, 'sigs': sorted(sigs, key=lambda s: (sorted(s[0]), s[1]))}
            elif n % 3 == 2:
                sigs = set()
                for X in vecs:
                    v = []
                    for t in range(K):
                        if X[t] >= CAP: continue
                        xx = list(X); xx[t] += 1
                        if mo(tuple(xx)): v.append(t)
                    mpair = mp(tuple(X))
                    oddk = tuple(i for i, c in enumerate(X) if c % 2 == 1)
                    sigs.add((frozenset(v), mpair, len(oddk), oddk))
                pre[n] = {'kind': 2, 'sigs': sorted(sigs, key=lambda s: (sorted(s[0]), s[1], s[2]))}
            else:
                oddvals = set(); zero = False; o1 = set(); all2 = False; one1 = set()
                for X in vecs:
                    if not mo(tuple(X)): continue
                    ok = [i for i, c in enumerate(X) if c % 2 == 1]
                    oddvals.add(len(ok))
                    if not ok: zero = True
                    if len(ok) == 1: o1.add(ok[0])
                    if all(c in (1, 2) for c in X):
                        if not ok: all2 = True
                        elif len(ok) == 1: one1.add(ok[0])
                pre[n] = {'kind': 0, 'exists': bool(oddvals), 'oddvals': oddvals,
                          'zero_odd': zero, 'odd1tiles': o1, 'all2': all2, 'one1': one1}
        return pre

    def lazy(self, cats, m):
        key = (tuple(cats), m)
        if key in self._c1: return self._c1[key]
        res = {'exists': False, 'oddvals': set(), 'zero_odd': False, 'odd1': set()}
        infos = [(c, self.pre_of(c)) for c in cats]
        def rec(i, rem, osum, allzero, owner):
            if i == len(infos):
                if rem == 0:
                    res['exists'] = True
                    res['oddvals'].add(osum)
                    if allzero: res['zero_odd'] = True
                    if owner is not None and osum == 1:
                        res['odd1'].add(self.g(owner[0], owner[1]))
                return
            c, pre = infos[i]
            for mj in range(0, rem + 1, 3):
                d = pre.get(mj)
                if not d or d.get('kind') != 0 or not d['exists']: continue
                if d['zero_odd']:
                    rec(i + 1, rem - mj, osum, allzero, owner)
                if owner is None:
                    for z in d['odd1tiles']:
                        rec(i + 1, rem - mj, osum + 1, False, (c, z))
                for o in d['oddvals']:
                    if o >= 2:
                        rec(i + 1, rem - mj, osum + o, False, None)
        rec(0, m, 0, True, None)
        self._c1[key] = res
        return res

    def lazy_all2_exists(self, c, s):
        key = ('a2', c, s)
        if key in self._c2: return self._c2[key]
        K = self.cat_kinds[c]; ok = False
        if s == 0:
            ok = True   # 空补牌族: 可拆面子的空多重集
        elif s % 2 == 0 and 2 <= s and (s // 2) <= K:
            k = s // 2
            for comb in itertools.combinations(range(K), k):
                v = [0] * K
                for i in comb: v[i] = 2
                if self._mo(tuple(v), c): ok = True; break
        self._c2[key] = ok; return ok

    def lazy_z_exists(self, c, s, lz):
        key = ('ze', c, s, lz)
        if key in self._c2: return self._c2[key]
        K = self.cat_kinds[c]; ok = False
        if (s - 1) % 2 == 0:
            k = (s - 1) // 2 + 1
            if 1 <= k <= K:
                rest = [i for i in range(K) if i != lz]
                for comb in itertools.combinations(rest, k - 1):
                    v = [0] * K; v[lz] = 1
                    for i in comb: v[i] = 2
                    if self._mo(tuple(v), c): ok = True; break
        self._c2[key] = ok; return ok

    def std_census(self):
        cen = set()
        for ci in range(self.nc):
            others = [c for c in range(self.nc) if c != ci]
            pre = self.pre_of(ci)
            for n in (1, 4, 7, 10, 13):
                m = 13 - n
                if not self.lazy(others, m)['exists']: continue
                for (wp, odd, oddk) in pre[n]['sigs']:
                    if wp: cen.add(frozenset(self.g(ci, t) for t in wp))
        for i in range(self.nc):
            for j in range(i + 1, self.nc):
                others = [c for c in range(self.nc) if c != i and c != j]
                for n1 in (2, 5, 8, 11):
                    for n2 in (2, 5, 8, 11):
                        m = 13 - n1 - n2
                        if m < 0 or not self.lazy(others, m)['exists']: continue
                        for (v1, mp1, o1, ok1) in self.pre_of(i)[n1]['sigs']:
                            Gv1 = frozenset(self.g(i, t) for t in v1)
                            for (v2, mp2, o2, ok2) in self.pre_of(j)[n2]['sigs']:
                                W = set()
                                if mp1: W.update(self.g(j, t) for t in v2)
                                if mp2: W.update(Gv1)
                                if W: cen.add(frozenset(W))
        return cen

    def loose_census(self):
        cen = self.std_census()
        for ci in range(self.nc):
            others = [c for c in range(self.nc) if c != ci]
            pre = self.pre_of(ci)
            for n in (1, 4, 7, 10, 13):
                m = 13 - n
                L = self.lazy(others, m)
                if not L['exists']: continue
                for (wp, odd, oddk) in pre[n]['sigs']:
                    base = frozenset(self.g(ci, t) for t in wp)
                    if base and any(o != 1 - odd for o in L['oddvals']): cen.add(base)
                    if odd == 1 and L['zero_odd']: cen.add(base | {self.g(ci, oddk[0])})
                    if odd == 0:
                        for z in L['odd1']: cen.add(base | {z})
        for i in range(self.nc):
            for j in range(i + 1, self.nc):
                others = [c for c in range(self.nc) if c != i and c != j]
                for n1 in (2, 5, 8, 11):
                    for n2 in (2, 5, 8, 11):
                        m = 13 - n1 - n2
                        if m < 0: continue
                        L = self.lazy(others, m)
                        if not L['exists']: continue
                        for (v1, mp1, o1, ok1) in self.pre_of(i)[n1]['sigs']:
                            Gv1 = frozenset(self.g(i, t) for t in v1)
                            for (v2, mp2, o2, ok2) in self.pre_of(j)[n2]['sigs']:
                                W = set()
                                if mp1: W.update(self.g(j, t) for t in v2)
                                if mp2: W.update(Gv1)
                                base = frozenset(W)
                                odd = o1 + o2
                                if base and any(o != 1 - odd for o in L['oddvals']): cen.add(base)
                                if odd == 1 and L['zero_odd']:
                                    zk = list(ok1) + list(ok2)
                                    if len(zk) == 1:
                                        z = self.g(i, zk[0]) if ok1 else self.g(j, zk[0])
                                        cen.add(base | {z})
                                if odd == 0:
                                    for z in L['odd1']: cen.add(base | {z})
        return cen

    def _act_vecs_z(self, c, k, lz):
        K = self.cat_kinds[c]
        rest = [i for i in range(K) if i != lz]
        out = []
        if k == 0: return out
        for comb in itertools.combinations(rest, k - 1):
            v = [0] * K; v[lz] = 1
            for i in comb: v[i] = 2
            out.append(tuple(v))
        return out

    def _act_vecs_all2(self, c, k):
        K = self.cat_kinds[c]
        out = []
        for comb in itertools.combinations(range(K), k):
            v = [0] * K
            for i in comb: v[i] = 2
            out.append(tuple(v))
        return out

    def _wp_of(self, v, c):
        K = len(v); off = self.offs[c]; wp = set()
        for t in range(K):
            if v[t] >= CAP: continue
            xx = list(v); xx[t] += 1
            if self._mp(tuple(xx), c): wp.add(off + t)
        return frozenset(wp)

    def _wstd2(self, v1, v2, c1, c2):
        W = set()
        if self._mp(tuple(v1), c1):
            for t in range(len(v2)):
                if v2[t] >= CAP: continue
                xx = list(v2); xx[t] += 1
                if self._mo(tuple(xx), c2): W.add(self.offs[c2] + t)
        if self._mp(tuple(v2), c2):
            for t in range(len(v1)):
                if v1[t] >= CAP: continue
                xx = list(v1); xx[t] += 1
                if self._mo(tuple(xx), c1): W.add(self.offs[c1] + t)
        return frozenset(W)

    def strict_census(self):
        cen = self.std_census()
        Kc = self.cat_kinds
        for z in range(self.nkinds):
            zc = self.cat_of(z)
            lz = z - self.offs[zc]
            for ks in itertools.product(*[range(0, Kc[c] + 1) for c in range(self.nc)]):
                if sum(ks) != 7 or ks[zc] < 1: continue
                tot = [2 * ks[c] - (1 if c == zc else 0) for c in range(self.nc)]
                if any(t < 0 for t in tot) or sum(tot) != 13: continue
                r = [t % 3 for t in tot]
                n1 = sum(1 for x in r if x == 1); n2 = sum(1 for x in r if x == 2)
                if n1 == 1 and n2 == 0:
                    ci = r.index(1)
                    if ci != zc: continue
                    lazy = [c for c in range(self.nc) if c != ci]
                    if not all(self.lazy_all2_exists(c, tot[c]) for c in lazy): continue
                    for v in self._act_vecs_z(ci, ks[ci], lz):
                        cen.add(self._wp_of(v, ci) | {z})
                elif n1 == 0 and n2 == 2:
                    act = [c for c in range(self.nc) if r[c] == 2]
                    lazy = [c for c in range(self.nc) if r[c] == 0]
                    ok = True
                    for c in lazy:
                        if c == zc:
                            if not self.lazy_z_exists(c, tot[c], lz): ok = False; break
                        else:
                            if not self.lazy_all2_exists(c, tot[c]): ok = False; break
                    if not ok: continue
                    vlists = []
                    for c in act:
                        if c == zc: vlists.append(self._act_vecs_z(c, ks[c], lz))
                        else: vlists.append(self._act_vecs_all2(c, ks[c]))
                    for v1 in vlists[0]:
                        for v2 in vlists[1]:
                            cen.add(self._wstd2(v1, v2, act[0], act[1]) | {z})
        return cen

    def win_std(self, c):
        for j in range(self.nkinds):
            if c[j] >= 2:
                cc = list(c); cc[j] -= 2
                good = True
                for ci in range(self.nc):
                    a = self.offs[ci]; b = a + self.cat_kinds[ci]
                    if not self._mo(tuple(cc[a:b]), ci): good = False; break
                if good: return True
        return False

    def win(self, c, mode='strict'):
        if self.win_std(c): return True
        if sum(c) == 14:
            if mode == 'strict':
                if sum(1 for x in c if x == 2) == 7: return True
            else:
                if all(x % 2 == 0 for x in c): return True
        if self.kokushi:
            if all(c[i] >= 1 for i in KOKUSHI_IDX) and sum(c) == 14 and all(c[i] <= 2 for i in KOKUSHI_IDX):
                return True
        return False


def brute_census(uni, mode='strict'):
    cen = set(); hands = 0
    for counts in gen_vectors(uni.nkinds, 13):
        c = list(counts)
        W = set()
        for t in range(uni.nkinds):
            if c[t] >= CAP: continue
            c[t] += 1
            if uni.win(c, mode): W.add(t)
            c[t] -= 1
        if W:
            hands += 1; cen.add(frozenset(W))
    return cen, hands


def brute_chiitoi_census(uni, mode='strict'):
    cen = set(); only = set()
    for combo in itertools.combinations(range(uni.nkinds), 7):
        for z in combo:
            c = [0] * uni.nkinds
            for i in combo: c[i] = 2
            c[z] = 1
            W = set(); Wstd = set()
            for t in range(uni.nkinds):
                if c[t] >= CAP: continue
                c[t] += 1
                if uni.win(c, mode): W.add(t)
                if uni.win_std(c): Wstd.add(t)
                c[t] -= 1
            if W: cen.add(frozenset(W))
            if not Wstd: only.add(z)
    return cen, only


def validate():
    out = []
    # 所有类别都是"可顺子"的抽象宇宙; 混合一个"字牌型"(无顺子)类别
    cases = [((3, 3, 2, 2), None), ((3, 3, 3, 2), None), ((4, 4, 3, 2), None),
             ((3, 3, 3, 2), [False, False, False, True]), ((4, 4, 3, 2), [False, False, False, True])]
    for cat_kinds, hon in cases:
        uni = Uni(cat_kinds, cat_is_honor=hon)
        for mode in ('strict', 'loose'):
            t0 = time.time()
            bcen, bhands = brute_census(uni, mode)
            cen_sig = uni.loose_census() if mode == 'loose' else uni.strict_census()
            _, only = brute_chiitoi_census(uni, mode)
            cen_sig2 = set(cen_sig) | {frozenset([z]) for z in only}
            missing = bcen - cen_sig2; extra = cen_sig2 - bcen
            row = {'cat_kinds': list(cat_kinds), 'honor': hon, 'mode': mode,
                   'brute_classes': len(bcen), 'brute_hands': bhands,
                   'sig_classes': len(cen_sig2), 'sig_raw': len(cen_sig),
                   'missing': len(missing), 'extra': len(extra),
                   'missing_examples': [sorted(x) for x in list(missing)[:5]],
                   'extra_examples': [sorted(x) for x in list(extra)[:5]],
                   'elapsed': round(time.time() - t0, 1)}
            out.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    return out


def flush_mode():
    out = []
    for cat_kinds, hon, name in [((9,), None, 'flush-1cat'), ((9, 9, 9, 7), [False, False, False, True], 'full')]:
        uni = Uni(cat_kinds, cat_is_honor=hon, kokushi=(name == 'full'))
        for mode in ('strict', 'loose'):
            t0 = time.time()
            if name == 'flush-1cat':
                cen = uni.strict_census() if mode == 'strict' else uni.loose_census()
                _, only = brute_chiitoi_census(uni, mode)
                cen = set(cen) | {frozenset([z]) for z in only}
                bc, bh = brute_census(uni, mode)
                row = {'name': name, 'mode': mode, 'sig': len(cen), 'brute': len(bc),
                       'hands_brute': bh, 'missing': len(bc - cen), 'extra': len(cen - bc),
                       'elapsed': round(time.time() - t0, 1)}
            else:
                cen = uni.strict_census() if mode == 'strict' else uni.loose_census()
                row = {'name': name, 'mode': mode, 'classes_raw': len(cen),
                       'elapsed': round(time.time() - t0, 1)}
            out.append(row); print(json.dumps(row, ensure_ascii=False), flush=True)
    return out


def full_mode():
    uni = Uni((9, 9, 9, 7), cat_is_honor=[False, False, False, True], kokushi=True)
    res = {}
    for mode in ('loose', 'strict'):
        t0 = time.time()
        cen = uni.loose_census() if mode == 'loose' else uni.strict_census()
        singles = {z for z in range(uni.nkinds) if frozenset([z]) in cen}
        cen2 = set(cen); cen2.add(frozenset(KOKUSHI_IDX))
        items = sorted(','.join(map(str, sorted(W))) for W in cen2)
        h = hashlib.sha256(('|'.join(items)).encode()).hexdigest()[:16]
        res[mode] = {'std_classes': len(uni.std_census()), 'raw': len(cen), 'total': len(cen2),
                     'singletons': len(singles), 'elapsed': round(time.time() - t0, 1), 'hash': h}
        print(mode, json.dumps(res[mode], ensure_ascii=False), flush=True)
        json.dump(sorted([sorted(W) for W in cen2]), open('work/verify/census_%s.json' % mode, 'w'))
    return res


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'flush'
    if cmd == 'validate': validate()
    elif cmd == 'flush': flush_mode()
    elif cmd == 'full': full_mode()
    else: print('unknown', cmd)
