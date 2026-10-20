
import json, collections
d=json.load(open(r"D:\DSH\MJ2\work\data\out\global.json"))
cls=d["classes"]
ns=sorted((len(c["sources"]), c["Wmask"], c["W"][:3]) for c in cls)
print("max sources:", ns[-1], "top10:", ns[-6:])
import statistics
print("total sources:", sum(x[0] for x in ns), "median:", statistics.median(x[0] for x in ns))
# how many classes have >2000 sources
print("classes with >1000 sources:", sum(1 for x in ns if x[0]>1000))
print("classes with >500 sources:", sum(1 for x in ns if x[0]>500))
print("classes with >200 sources:", sum(1 for x in ns if x[0]>200))
