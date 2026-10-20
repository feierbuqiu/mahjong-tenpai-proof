import json, collections
d = json.load(open(r'D:\DSH\MJ2\work\verify\plan_k4_FINAL.json', encoding='utf-8'))
cs = [tuple(c) for r in d['plan'] for c in r['codes']]
print('total', len(cs), 'distinct', len(set(cs)))
print('top dups', collections.Counter(cs).most_common(5))
def enc(t):
    a = 0
    for x in t: a = a * 34 + x
    return a
es = collections.Counter(enc(t) for t in cs)
print('enc distinct', len(es), 'enc dups', sum(v-1 for v in es.values() if v > 1))
# also: how many plan rows share the same code list?
rows = [tuple(tuple(c) for c in r['codes']) for r in d['plan']]
print('distinct code-lists', len(set(rows)), 'of', len(rows))
