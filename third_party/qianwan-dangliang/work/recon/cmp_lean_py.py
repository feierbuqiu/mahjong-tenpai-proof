# -*- coding: utf-8 -*-
import sys
sys.path.insert(0,'work/verify')
from indep_core import compute_W
ins=[l.strip() for l in open('work/lean_hand_input.txt',encoding='utf-8') if l.strip()]
outs=[l.strip() for l in open('work/lean_hand_output.txt',encoding='utf-8')]
print("inputs",len(ins),"outputs",len(outs))
bad=0; tenpai=0
for a,b in zip(ins,outs):
    v=[int(x) for x in a.split(',')]
    lw=set(int(x) for x in b.split(',') if x!='')
    pw=set(compute_W(v))
    if pw: tenpai+=1
    if lw!=pw:
        bad+=1
        if bad<=5: print("MISMATCH", v, sorted(lw), sorted(pw))
print("tenpai hands", tenpai, "mismatches", bad)
