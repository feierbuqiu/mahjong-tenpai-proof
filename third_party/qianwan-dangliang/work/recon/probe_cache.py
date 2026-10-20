
import numpy as np
z=np.load(r"D:\DSH\MJ2\work\verify\cache_w_p.npz")
print("files:", z.files)
for k in z.files:
    a=z[k]
    print("  ",k, a.dtype, a.shape, a[:3] if a.ndim==1 else a[:2])
