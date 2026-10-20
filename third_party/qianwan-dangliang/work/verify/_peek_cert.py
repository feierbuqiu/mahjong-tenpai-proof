
import json
c = json.load(open("work/lowerbound/certificate.json", encoding="utf-8"))
def keys(d, pre=""):
    if isinstance(d, dict):
        for k, v in d.items():
            t = type(v).__name__
            extra = ""
            if isinstance(v, (int, float, str, bool)) or v is None: extra = " = " + str(v)[:80]
            elif isinstance(v, list): extra = " len=" + str(len(v))
            elif isinstance(v, dict): extra = " keys=" + str(list(v.keys())[:8])
            print(pre + k + " (" + t + ")" + extra)
            if isinstance(v, dict): keys(v, pre + "  ")
print("top keys:", list(c.keys()))
for k in c:
    if k != "theorems": keys({k: c[k]})
t = c["theorems"]
print("theorems keys:", list(t.keys()))
for k in t:
    row = t[k]
    print("---", k, {kk: (str(vv)[:60] if not isinstance(vv, list) else "list len=%d" % len(vv)) for kk, vv in row.items()})
# sample class row
cc = t["k=2"]["classes"][:2]
print(json.dumps(cc, ensure_ascii=False)[:900])
