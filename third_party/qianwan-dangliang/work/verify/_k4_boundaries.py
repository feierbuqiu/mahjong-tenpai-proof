
import sys
sys.path.insert(0, "work/verify")
from indep_core import is_win_std_fast, melds_only_honor, melds_only, compute_W, is_win_full

def H(d):
    c=[0]*34
    for k,v in d.items(): c[k]=v
    return c

# (a) 字牌不能有顺子
c1 = H({0:3, 2:3, 4:3, 6:2, 27:1, 28:1, 29:1})   # 111m 333m 555m + 77m + E S W  (=14)
c2 = H({0:3, 2:3, 4:3, 6:2, 27:3})                # 111m 333m 555m + 77m + EEE  (=14)
print("E,S,W 当作顺子 -> win?", is_win_std_fast(c1), "(应为 False)")
print("EEE 刻子      -> win?", is_win_std_fast(c2), "(应为 True)")
print("melds_only_honor((1,1,1,0,0,0,0)) =", melds_only_honor((1,1,1,0,0,0,0)), "(应为 False)")
print("melds_only_honor((3,0,0,0,0,0,0)) =", melds_only_honor((3,0,0,0,0,0,0)), "(应为 True)")
# 反例: 如果允许字牌顺子, c1 会被判成和牌; 检查它对 W 的影响
h_hand = H({0:3, 2:3, 4:3, 6:2, 27:1, 28:1})      # 13 张: 111m 333m 555m 77m E S
print("W(111m333m555m77m E S) =", sorted(compute_W(h_hand)), "(不应包含通过字牌顺子构成的听牌)")

# (b) k=4 下 chiitoi 手牌的最大重数: 严格七对子听牌手 = 6 对 + 单张
chi = H({0:1, 1:2, 2:2, 3:2, 4:2, 5:2, 6:2})       # 1m + 2m..7m 各一对 = 13 张
print("chiitoi hand counts max:", max(chi), " -> 任何码若含某牌 3 张或 4 张都装不进该手牌")
def fits(hand, code):
    from collections import Counter
    need = Counter(code)
    return all(hand[t] >= v for t, v in need.items())
print("code (2m,2m,2m,2m) subset?", fits(chi,(2,2,2,2)), "(应 False)")
print("code (2m,2m,3m,3m) subset?", fits(chi,(2,2,3,3)), "(应 True)")
print("code (1m,1m,1m,1m) subset?", fits(chi,(0,0,0,0)), "(应 False, 1m 只有 1 张)")
