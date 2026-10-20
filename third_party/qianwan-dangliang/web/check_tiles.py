# -*- coding: utf-8 -*-
"""check_tiles.py -- 校验 HTML 内联的牌面图与 web/pai-images 源文件逐张一致(哈希)."""
import json, re, base64, hashlib, os, sys
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
HERE = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(HERE, "mahjong_demo.html"), encoding="utf-8").read()
IMG = json.loads(re.search(r"var TILE_SRC=(\{.*?\});", html, re.S).group(1))
IMGE = json.loads(re.search(r"var TILE_SRC_EMB=(\{.*?\});", html, re.S).group(1))
PAI = os.path.join(HERE, "pai-images")
SP = {0: "man", 1: "pin", 2: "sou"}
HJ = {27: "ji1", 28: "ji2", 29: "ji3", 30: "ji4", 31: "ji6", 32: "ji5", 33: "ji7"}
NAMES = ["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","7p","8p","9p",
         "1s","2s","3s","4s","5s","6s","7s","8s","9s","E","S","W","N","Haku","Hatsu","Chun"]
bad = []
for t in range(34):
    f = (("%s%d-66-90-l" % (SP[t//9], t%9+1)) if t < 27 else HJ[t] + "-66-90-l")
    for suf, d in ((".png", IMG), ("-emb.png", IMGE)):
        want = open(os.path.join(PAI, f + suf), "rb").read()
        got = base64.b64decode(d[str(t)].split(",", 1)[1])
        if hashlib.sha256(want).hexdigest() != hashlib.sha256(got).hexdigest():
            bad.append((NAMES[t], f + suf))
print("内联牌面数: %d (+%d 高亮变体) ; 与源文件不一致: %s" % (len(IMG), len(IMGE), bad if bad else "无 ✓"))
print("data URI 出现次数:", html.count("data:image/png;base64,"))
print("HTML 大小: %.0f KB (其中图片 ~%.0f KB, 策略表 ~%.0f KB)"
      % (len(html)/1024, sum(len(v) for v in IMG.values())/1024 + sum(len(v) for v in IMGE.values())/1024, 256273/1024))
print("牌面映射示例: 東=%s 白=%s 發=%s 中=%s"
      % (HJ[27], HJ[31], HJ[32], HJ[33]))
