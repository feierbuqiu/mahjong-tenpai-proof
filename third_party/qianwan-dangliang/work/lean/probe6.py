import json, re, collections
src = open(r'D:\DSH\MJ2\lean\Mj\Data.lean', encoding='utf-8').read()
# extract planChunk definitions
parts = []
for m in re.finditer(r'^def planChunk(\d+) : List \(List Nat × List \(List Nat\)\) := (.*)$', src, re.M):
    parts.append((int(m.group(1)), m.group(2)))
parts.sort()
print("planChunk defs:", len(parts), [p[0] for p in parts][:20])
body = " + ".join(p[1] for p in parts)
data = eval(body)
print("parsed rows:", len(data))
codes = [tuple(c) for (k, cs) in data for c in cs]
print("parsed codes:", len(codes), "distinct:", len(set(codes)))
d = json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json', encoding='utf-8'))
jc = [tuple(c) for r in d['plan'] for c in r['codes']]
print("json codes:", len(jc), "distinct:", len(set(jc)))
print("counter sample (Lean):", collections.Counter(codes).most_common(5))
def enc(t):
    a = 0
    for x in t: a = a * 34 + x
    return a
print("len mismatches:", sum(1 for c in codes if len(c) != 4))
print("first row leans:", data[0][0], data[0][1][:3])
