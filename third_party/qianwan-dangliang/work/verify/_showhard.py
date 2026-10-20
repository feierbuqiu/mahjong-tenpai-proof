
import json
d = json.load(open("work/verify/plan_k4_final.json", encoding="utf-8"))
ff = d["finalfix"]
hard = ff.get("typeI_hard_all", [])
print("typeI_hard_all:", len(hard))
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]
for h in hard[:10]:
    print("   ", h)
