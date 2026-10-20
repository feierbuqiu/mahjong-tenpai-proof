# -*- coding: utf-8 -*-
"""stat_sources.py -- 从 classes.tsv 统计每类的来源块数/个体来源数(用于评估覆盖规模)"""
import re, sys, os, json
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "classes.tsv")
tot_blocks = 0; tot_src = 0
per_class = []
maxrec = None
for line in open(p, encoding="utf-8"):
    line = line.rstrip("\n")
    if not line: continue
    W, srcs = line.split("\t")
    recs = srcs.split(";")
    nb = len(recs); ns = 0
    for r in recs:
        m = re.findall(r"(\d+)$", r)
        ns += int(m[0]) if m else 0
    tot_blocks += nb; tot_src += ns
    per_class.append((len(W.split(",")) if W else 0, nb, ns))
    if maxrec is None or ns > maxrec[2]: maxrec = (W, nb, ns)
dist = {}
for _, nb, ns in per_class:
    b = "src<=1" if ns <= 1 else "2-5" if ns <= 5 else "6-20" if ns <= 20 else "21-100" if ns <= 100 else "101-1000" if ns <= 1000 else "1001-10000" if ns <= 10000 else ">10000"
    dist[b] = dist.get(b, 0) + 1
print("类数=%d  Σ块数=%d  Σ个体来源=%d" % (len(per_class), tot_blocks, tot_src))
print("个体来源数分布:", dist)
print("最大来源类: |W|=%d 块=%d 来源=%d" % (maxrec[0].count(",") + 1 if maxrec[0] else 0, maxrec[1], maxrec[2]))
import statistics
srcs = sorted(x[2] for x in per_class)
print("来源数分位: p50=%d p90=%d p99=%d max=%d" % (srcs[len(srcs)//2], srcs[int(len(srcs)*0.9)], srcs[int(len(srcs)*0.99)], srcs[-1]))
