
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\recon\k4_subuniverse_covers.json"))
per=collections.Counter(); tot=0; bad=0
LETTER="mpsz"
for k,v in d.items():
    per[v["letter"]]+=len(v["codes"]); tot+=len(v["codes"])
    for c in v["codes"]:
        cs={ (t//9 if t<27 else 3) for t in c }
        if len(cs)!=1 or LETTER[list(cs)[0]]!=v["letter"]: bad+=1
print("classes:",len(d),"total codes:",tot,"per letter:",dict(per),"codes outside their suit:",bad)
print("sample:", json.dumps(list(d.items())[0], ensure_ascii=False)[:300])
