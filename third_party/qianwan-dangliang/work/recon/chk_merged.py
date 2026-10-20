
import json, collections
p=json.load(open(r"D:\DSH\MJ2\work\recon\plan_k4_merged.json"))["plan"]
allc=[tuple(c) for e in p for c in e["codes"]]
print("classes:",len(p),"codes:",len(allc),"distinct:",len(set(allc)),"dups:",len(allc)-len(set(allc)),"empty:",sum(1 for e in p if not e["codes"]))
