# -*- coding: utf-8 -*-
"""xcheck_lean_waits.py -- Lean 的 waits 与 Python(已验证 indep_core.compute_W) 对拍"""
import sys, os
sys.path.insert(0, 'work/verify')
from indep_core import compute_W
bad=0; n=0
for line in open('work/lean_waits_sample.txt', encoding='utf-8'):
    line=line.strip()
    if not line or '|' not in line: continue
    a,b=line.split('|')
    counts=[int(x) for x in a.split(',')] if a else []
    lw=set(int(x) for x in b.split(',') if x!='')
    pw=set(compute_W(counts))
    n+=1
    if lw!=pw:
        bad+=1
        if bad<=5: print("MISMATCH counts=%s lean=%s py=%s" % (counts, sorted(lw), sorted(pw)))
print("compared %d hands, mismatches %d" % (n, bad))
