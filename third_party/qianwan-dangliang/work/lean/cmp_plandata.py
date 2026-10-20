import json
HONN=['E','S','W','N','Haku','Hatsu','Chun']
def ti(s): return 27+HONN.index(s) if s in HONN else 'mps'.index(s[-1])*9+int(s[0])-1
P=json.load(open('work/verify/plan_k4_FINAL.json',encoding='utf-8'))
plan={tuple(sorted(ti(x) for x in r['W'])):[tuple(c) for c in r['codes']] for r in P['plan']}
lean={}
for line in open('work/lean_plandata_dump.txt',encoding='utf-8'):
    line=line.strip()
    if not line: continue
    a,b=line.split('|')
    k=tuple(int(x) for x in a.split(','))
    cs=[tuple(int(x) for x in c.split(',')) for c in b.split(';') if c]
    lean[k]=cs
print('py classes',len(plan),'lean classes',len(lean))
print('keys only py',len(set(plan)-set(lean)),'only lean',len(set(lean)-set(plan)))
diff=sum(1 for k in set(plan)&set(lean) if sorted(plan[k])!=sorted(lean[k]))
print('classes with differing codes',diff)
print('CONSISTENT:', set(plan)==set(lean) and diff==0)
