import json, re, collections
src = open(r'D:\DSH\MJ2\lean\Mj\Data.lean', encoding='utf-8').read()
# capture from "def planChunkN ... := " until the next top-level "def " at line start
pat = re.compile(r'^def planChunk(\d+) : List \(List Nat × List \(List Nat\)\) := (.*?)(?=^def |\Z)', re.M | re.S)
parts = sorted((int(m.group(1)), m.group(2)) for m in pat.finditer(src))
print("chunks:", len(parts), [p[0] for p in parts])
data = []
for idx, body in parts:
    d = eval(body.strip())
    data += d
print("rows", len(data), "codes", sum(len(cs) for (k, cs) in data))
codes = [tuple(c) for (k, cs) in data for c in cs]
print("distinct codes", len(set(codes)), "dups", len(codes) - len(set(codes)))
counter = collections.Counter(codes)
print("top dup codes", counter.most_common(5))
d2 = json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json', encoding='utf-8'))
HON = ["E","S","W","N","Haku","Hatsu","Chun"]; HONI = {n: 27+i for i,n in enumerate(HON)}
def to_idx(x):
    if isinstance(x, int): return x
    if x in HONI: return HONI[x]
    return "mps".index(x[-1])*9 + int(x[0]) - 1
json_rows = [(sorted(to_idx(x) for x in r["W"]), [tuple(c) for c in r["codes"]]) for r in d2["plan"]]
lean_rows = [(list(k), [tuple(c) for c in cs]) for (k, cs) in data]
print("row counts", len(lean_rows), len(json_rows))
bad = 0
for i in range(min(len(lean_rows), len(json_rows))):
    if lean_rows[i] != json_rows[i]:
        bad += 1
        if bad <= 3:
            print("MISMATCH row", i, "lean key", lean_rows[i][0], "json key", json_rows[i][0],
                  "ncodes", len(lean_rows[i][1]), len(json_rows[i][1]))
            print("  lean first3", lean_rows[i][1][:3], "json first3", json_rows[i][1][:3])
print("mismatched rows:", bad)
