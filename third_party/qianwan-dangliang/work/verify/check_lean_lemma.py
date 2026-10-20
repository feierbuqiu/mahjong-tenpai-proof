
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_lean_lemma.py -- task-11 静态验收: 禁用词 / 语句形状 / 冻结文件未被改动.
(动态验收 lake build 与 #print axioms 由 verifier 单独跑)
"""
import re, os, sys, hashlib
HERE=os.path.dirname(os.path.abspath(__file__))
ROOT=os.path.join(HERE,"..","..")
F=os.path.join(ROOT,"lean","Mj","Lemma.lean")
src=open(F,encoding="utf-8").read()
print("file:",F,"lines:",src.count("\n")+1)
# 去掉注释行里的干扰 (简单处理: 逐行去掉 -- 之后内容)
code_lines=[]
for ln in src.splitlines():
    code_lines.append(ln.split("--")[0])
code="\n".join(code_lines)
bad=[tok for tok in ["axiom","sorry","admit","native_decide","unsafe","set_option maxHeartbeats 0"] if re.search(r"\b"+re.escape(tok)+r"\b", code)]
print("禁用词:", bad if bad else "无 ✓")
for name in ["budget","classes_le_pow","no_common_code_two","codesU_nodup","codesU_length","mem_codesU"]:
    print("  含 %-22s %s" % (name, ("是" if name in code else "**否**")))
for hyp in ["hcls","hSnodup","hdisj","hlen","hsub","hU"]:
    print("  含假设 %-8s %s" % (hyp, ("是" if hyp in code else "**否**")))
concl="(cls.map List.length).sum ≤ U.length ^ k"
print("  结论形状 %r: %s" % (concl, "是" if concl.replace(" ","") in code.replace(" ","") else "**否**"))
# 冻结文件哈希对比
snap=os.path.join(HERE,"_lean_frozen_hashes.txt")
if os.path.exists(snap):
    ok=True
    for line in open(snap,encoding="utf-8").read().splitlines():
        p,h=line.rsplit(" ",1)
        fp=os.path.join(ROOT,p)
        cur=hashlib.sha256(open(fp,"rb").read()).hexdigest() if os.path.exists(fp) else "MISSING"
        if cur!=h: print("  冻结文件被改动:",p); ok=False
    print("冻结文件(Frozen)未改动:", ok)
