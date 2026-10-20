
import os,time
d="work/lowerbound"
fs=[(os.path.getmtime(os.path.join(d,f)),f) for f in os.listdir(d)]
fs.sort(reverse=True)
now=time.time()
for m,f in fs[:8]:
    print("%6.1f min ago  %s" % ((now-m)/60, f))
