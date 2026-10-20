
import json
p = json.load(open("work/verify/plan_k4_final.json", encoding="utf-8"))
print("keys:", list(p.keys()))
print("n_codes:", p.get("n_codes"), "classes:", p.get("n_classes"))
print("has finalfix:", "finalfix" in p, " has swapfix:", "swapfix" in p)
if "finalfix" in p: print("finalfix typeI_hard:", p["finalfix"].get("typeI_hard"), " hard_all len:", len(p["finalfix"].get("typeI_hard_all", [])))
if "swapfix" in p: print("swapfix:", json.dumps(p["swapfix"], ensure_ascii=False)[:400])
