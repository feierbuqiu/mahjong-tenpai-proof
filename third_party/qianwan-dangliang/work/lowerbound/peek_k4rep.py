import json, sys
sys.stdout.reconfigure(encoding="utf-8")
R = json.load(open("work/lowerbound/verify_k4_baseline.json", encoding="utf-8"))
for k in ("plan","k","n_classes","n_codes","check1_symdiff","check2_empty_classes","check3_code_collisions",
          "check3_multiset_over_capacity","check3_max_use","check4_unverified","check4_via",
          "check4_tanki_sample_witness_fail","check5_typeI_blocks_scanned","check5_typeI_uncovered",
          "check6_chiitoi_descriptors","check6_chiitoi_fail","check7_kokushi_fail","check8_sim_target",
          "check8_sim_result","VERDICT_k4_plan_ok"):
    print(k, "=", json.dumps(R.get(k), ensure_ascii=False)[:300])
print()
print("no_class 例:")
for e in R.get("check8_no_class_examples", []): print("   W=%s  hand=%s" % (e["W"], e["hand"]))
print()
print("chiitoi 失败例:", json.dumps(R.get("check6_chiitoi_fail_examples", [])[:3], ensure_ascii=False))
