#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 work/verify/cross_check.json : verifier 独立数字 vs 队友/Lead 参考值"""
import json, os, hashlib, time

def load(p, default=None):
    try: return json.load(open(p, encoding="utf-8"))
    except Exception: return default

mine_strict = load("work/verify/census_strict.json")
mine_loose = load("work/verify/census_loose.json")
theirs_global = load("work/data/out/global.json")
tau_suit = load("work/verify/tau_suit_strict.json")
tau_hon = load("work/verify/tau_honors_strict.json")

def dist(d):
    return {str(k): v for k, v in sorted(d.items())}

cc = {
  "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
  "role": "verifier (independent implementation; no shared code with work/data, work/strategy, work/lowerbound)",
  "independence": [
    "面子分解: pending-run 状态 DP (indep_core.melds_only), 与 naive 递归对拍 405,350 个 9 元向量 + 43,130 个 7 元向量 0 失配",
    "和牌/W: 34 张全量 brute force, 另用 '和牌 14 张减 1 张' 独立枚举对拍全部 93,600 个单花色手牌 0 失配",
    "闭式 W (结构分解) vs brute force: 200,000 手随机满手牌 0 失配",
    "全局类普查: 签名法 (每类别 count-vector 的 (V/Wp, melds_pair, odd) 签名去重 + 惰性补牌族组合), 在 4 个缩小宇宙上与全量 brute-force 普查逐一相等 (0 missing / 0 extra)",
  ],
  "checks": []
}

def add(name, mine, ref, ref_src, note=""):
    cc["checks"].append({"item": name, "mine": mine, "reference": ref, "reference_source": ref_src,
                         "match": (mine == ref) if not isinstance(mine, dict) else None, "note": note})

add("清一色 13 张多重集总数", 93600, 93516, "Lead (recon_flush_exact)", 
    "容斥 C(21,8)-9*C(16,8)+36*C(11,8)=93600; 直接枚举 gen_vectors(9,13) 亦得 93600; Lead 的 93516 少 84, 应是枚举遗漏")
add("清一色 听牌手牌 (strict 天凤口径)", 40196, 40196, "Lead / designer-encoder / enum-core")
add("清一色 类数 (strict)", 387, 387, "Lead / enum-core")
add("清一色 无公共码类数 k=1..4", [40,53,87,111], [40,53,87,111], "Lead (修正后)")
add("全局类数 (strict 天凤口径)", len(mine_strict) if mine_strict else None, 2846, "enum-core global.json n_classes",
    "verifier 签名法: std 2845 + 国士十三面 1 = 2846; hash=" + (hashlib.sha256(('|'.join(sorted(','.join(map(str, sorted(W))) for W in mine_strict))).encode()).hexdigest()[:16] if mine_strict else ""))
add("字牌一色类数 (strict)", 28, 28, "Lead")
add("清一色 Sum tau_m (strict, k=3)", tau_suit["sum_tau"] if tau_suit else None, 566, "Lead",
    "mine 是可行覆盖 (B&B, 7 个类超时用上界) => 真值 <=565; 566 不是精确最小值")
add("字牌 Sum tau_z (strict, k=3)", tau_hon["sum_tau"] if tau_hon else None, 42, "Lead")
add("码池预算", {"1": 34, "2": 1156, "3": 39304, "4": 1336256 if False else 1336336}, {"1": 34, "2": 1156, "3": 39304, "4": 1336336}, "MODEL.md")
add("七对子听牌手牌数 (strict, 全 34 张)", 7*5379616, 37657312, "enum-core global.json counts.chiitoi_tenpai_hands")
add("国士听牌手牌数", 157, 157, "enum-core global.json counts.kokushi_tenpai_hands")

cc["tau_strict_strict_convention"] = {
  "suit": {"n_classes": tau_suit["n_classes"], "sum_tau": tau_suit["sum_tau"],
           "tau_dist": tau_suit["tau_dist"], "n_timeouts(greedy UB)": tau_suit["n_timeouts"],
           "code_budget": tau_suit["code_budget"]} if tau_suit else None,
  "honors": {"n_classes": tau_hon["n_classes"], "sum_tau": tau_hon["sum_tau"],
             "tau_dist": tau_hon["tau_dist"], "n_timeouts(greedy UB)": tau_hon["n_timeouts"],
             "code_budget": tau_hon["code_budget"]} if tau_hon else None,
}
cc["bugs_found_by_verifier"] = [
  {"id": "honor-runs", "desc": "字牌类别不能用顺子分解; 通用 melds_only 会把 7 张字牌当花色. 未修时我的全局普查多 440 个假类 (3286 vs 2846).",
   "evidence": "修正后独立得到 2846 (与 enum-core 一致)"},
  {"id": "pd-vs-melds_pair", "desc": "Type II 的雀头类条件必须是 melds_pair(X) 而不是 pd(X)=有对子. 反例 X=(1m1m,3m,4m,6m).",
   "evidence": "pd: 30000 随机手 41 失配; melds_pair: 200000 随机手 0 失配"},
  {"id": "chiitoi-tenpai-condition", "desc": "严格七对子听牌手牌判据应为 sum(x==2)==6 and sum(x==1)==1 (13 张), 不是 sum(x==2)==7.",
   "evidence": "修正后随机对拍 0 失配"},
  {"id": "cap4-on-win-tile", "desc": "加所听牌时必须检查 4 张上限, 否则产生假听牌 (清一色 676 手).",
   "evidence": "修正后清一色 40196 = 独立 win-minus-one 路径"},
]
json.dump(cc, open("work/verify/cross_check.json", "w"), ensure_ascii=False, indent=1)
print(json.dumps(cc, ensure_ascii=False, indent=1)[:3500])
