#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""fastcov_k3.py <plan_k3.json> -- k=3 单花色全量覆盖复验 (复用 fastcov 的缓存与向量化内核)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fastcov
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "work/strategy/out/plan_k3.json"
    res = fastcov.gap(path, "--rebuild" in sys.argv)
    for name in ("m", "p", "s", "z"):
        r = res["suits"][name]
        print(name, "classes_with_failures", r["classes_with_failures"],
              "uncovered_coded", r["uncovered_in_coded_classes"],
              "uncovered_zero_code", r["uncovered_in_zero_code_classes"])
    json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "fastcov_report_k3.json"), "w"),
              ensure_ascii=False, indent=1)
    print("total uncovered:", sum(v["uncovered_in_coded_classes"] + v["uncovered_in_zero_code_classes"] for v in res["suits"].values()))
