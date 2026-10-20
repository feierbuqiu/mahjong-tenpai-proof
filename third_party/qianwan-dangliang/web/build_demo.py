# -*- coding: utf-8 -*-
"""build_demo.py -- 由 work/verify/plan_k4_FINAL.json 生成单文件离线 HTML 演示。
输出: web/mahjong_demo.html
"""
import json, os, collections, base64
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PLAN = os.path.join(ROOT, "work", "verify", "plan_k4_FINAL.json")
HONN = ["E","S","W","N","Haku","Hatsu","Chun"]; HON = {n:27+i for i,n in enumerate(HONN)}
def to_idx(w):
    o=[]
    for x in w:
        if isinstance(x,int): o.append(x)
        elif x in HON: o.append(HON[x])
        else: o.append("mps".index(x[-1])*9 + int(x[0]) - 1)
    return o
P = json.load(open(PLAN, encoding="utf-8"))
rows = P["plan"] if isinstance(P, dict) and "plan" in P else P
table = {}
ncodes = 0
for r in rows:
    W = to_idx(r["W"]); m = 0
    for t in W: m += 1 << t
    codes = [list(map(int, c)) for c in r["codes"]]
    table[str(m)] = codes
    ncodes += len(codes)
tbl = json.dumps(table, separators=(",", ":"), ensure_ascii=False)
print("classes:", len(table), "codes:", ncodes, "table bytes:", len(tbl))

# ---- 牌面图片素材(web/pai-images) -> base64 data URI 内联, 保持单文件离线 ----
PAI = os.path.join(HERE, "pai-images")
SP = {0: "man", 1: "pin", 2: "sou"}
HJ = {27: "ji1", 28: "ji2", 29: "ji3", 30: "ji4", 31: "ji6", 32: "ji5", 33: "ji7"}  # 注意: ji5=發, ji6=白
def tile_file(t, emb=False):
    if t < 27:
        name = "%s%d-66-90-l" % (SP[t // 9], t % 9 + 1)
    else:
        name = HJ[t] + "-66-90-l"
    return name + ("-emb.png" if emb else ".png")
def b64(name):
    with open(os.path.join(PAI, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode("ascii")
IMG = {str(t): b64(tile_file(t)) for t in range(34)}
IMGE = {str(t): b64(tile_file(t, True)) for t in range(34)}
missing = [t for t in range(34) if len(IMG[str(t)]) < 100 or len(IMGE[str(t)]) < 100]
JS_TILES = ("var TILE_SRC=" + json.dumps(IMG, separators=(",", ":")) + ";\n"
            "var TILE_SRC_EMB=" + json.dumps(IMGE, separators=(",", ":")) + ";")
print("tiles embedded:", len(IMG), "x2 ; missing:", missing, "; tiles js bytes:", len(JS_TILES))

HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>麻将「翻牌猜听牌」演示（k=4 策略）</title>
<style>
:root{--bg:#12241c;--panel:#1b3a2c;--tile:#f7f1df;--ink:#20301f;--hi:#ffd56b;--blue:#7ac6ff;--red:#d33a3a;}
*{box-sizing:border-box}
body{margin:0;padding:18px;background:linear-gradient(#0e1f18,#12241c);color:#e9f3ec;font-family:"Segoe UI",system-ui,"Microsoft YaHei",sans-serif}
h1{font-size:20px;margin:0 0 4px}
h2{font-size:15px;margin:18px 0 8px;color:#bfe6cf}
.sub{color:#9fc4ad;font-size:13px;margin-bottom:14px}
.panel{background:var(--panel);border:1px solid #2c5a45;border-radius:12px;padding:14px;margin-bottom:14px}
button{background:#2f7d5b;color:#fff;border:0;border-radius:8px;padding:8px 14px;font-size:14px;cursor:pointer;margin-right:8px}
button:hover{background:#3b9a70}
button.alt{background:#28506b}
button.alt:hover{background:#33688c}
input[type=text]{background:#0f2a20;color:#eafff3;border:1px solid #3a6f57;border-radius:8px;padding:8px 10px;font-size:15px;width:260px;font-family:ui-monospace,Consolas,monospace}
.row{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin:8px 0}
.tile{display:inline-block;width:46px;height:63px;border-radius:7px;background:var(--tile);
  box-shadow:0 2px 4px rgba(0,0,0,.45);user-select:none;position:relative;overflow:hidden}
.tile img{width:100%;height:100%;display:block;border-radius:7px}
.tile.small{width:34px;height:46px}
.tile.code{outline:3px solid var(--hi);box-shadow:0 0 12px var(--hi)}
.tile.flip{outline:3px solid var(--blue);box-shadow:0 0 12px var(--blue)}
.tile.code img{filter:brightness(1.06) saturate(1.05)}
.tile.pick{cursor:pointer;opacity:.95}
.tile.pick:hover{transform:translateY(-3px)}
.tile.dis{opacity:.25}
.slot{min-height:64px;display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.waits{font-size:16px}
.waits b{color:var(--hi)}
.msg{font-size:13px;color:#9fc4ad}
.bad{color:#ff9c9c}.good{color:#8ef0b2}
pre{background:#0f2a20;border:1px solid #3a6f57;border-radius:8px;padding:10px;overflow:auto;font-size:12px;max-height:200px}
label{font-size:13px;color:#bfe6cf;margin-right:8px}
</style>
</head>
<body>
<h1>麻将「翻牌猜听牌」演示 · 策略 k = 4</h1>
<div class="sub">A 把 13 张排成一行（把该类的 <b>4 元码</b>放在最左 4 位）；B 只翻开最左 4 张，就能唯一确定 A 的全部听牌。
本页表来自 <code>work/verify/plan_k4_FINAL.json</code>（2,846 类 / 17,579 条码），离线单文件、无外部依赖。</div>

<div class="panel">
  <h2>① 随机生成（门清 13 张，必为听牌）</h2>
  <button id="btnRandom">随机生成听牌手牌</button>
  <button id="btnSelfTest" class="alt">自测 100 次</button>
  <span id="selfTestMsg" class="msg"></span>
  <div class="row"><span class="msg">A 的排序：</span><div id="rowA" class="slot"></div></div>
  <div class="row"><span class="msg">B 翻开最左 4 张：</span><div id="rowB" class="slot"></div></div>
  <div class="waits" id="waitsOut"></div>
  <div class="msg" id="infoOut"></div>
</div>

<div class="panel">
  <h2>② 自定义手牌</h2>
  <label>输入（例：<code>123m456p789s11z22z</code> 或 <code>1m1m1m2m3m4m5m6m7m8m9m9m9m</code>）</label>
  <input type="text" id="custom" value="123m456p789s11z22z">
  <button id="btnApply">应用</button>
  <button id="btnClear" class="alt">清空</button>
  <span id="customMsg" class="msg"></span>
  <div class="msg" style="margin-top:6px">点选加牌（已满 4 张变灰）：</div>
  <div id="palette" class="row"></div>
  <div class="row"><span class="msg">当前手牌：</span><div id="rowC" class="slot"></div></div>
  <div class="waits" id="customWaits"></div>
  <div class="row"><span class="msg">A 的排序（自定义手牌）：</span><div id="rowA2" class="slot"></div></div>
  <div class="row"><span class="msg">B 翻开最左 4 张：</span><div id="rowB2" class="slot"></div></div>
  <div class="waits" id="customLookup"></div>
  <div class="msg" id="customInfo"></div>
</div>

<div class="panel">
  <h2>③ 自测详情</h2>
  <pre id="log">点「自测 100 次」：随机生成 100 手听牌，逐手验证「翻最左 4 张 → 查表得到的听牌 == 真实听牌」。</pre>
</div>

<script id="core">
/* ===== 麻将核心（口径与 Python mjlib 一致：标准型 / 严格七对子 / 国士） ===== */
var MJ = (function(){
  var CATBASE=[0,9,18,27], CATLEN=[9,9,9,7];
  var KOK=[0,8,9,17,18,26,27,28,29,30,31,32,33];
  var NAMES=["1m","2m","3m","4m","5m","6m","7m","8m","9m","1p","2p","3p","4p","5p","6p","7p","8p","9p",
             "1s","2s","3s","4s","5s","6s","7s","8s","9s","E","S","W","N","Haku","Hatsu","Chun"];
  function sum(c){var s=0;for(var i=0;i<34;i++)s+=c[i];return s;}
  function canMelds(seg,honors){
    var i=0;while(i<seg.length&&seg[i]===0)i++;
    if(i===seg.length)return true;
    if(seg[i]>=3){var a=seg.slice();a[i]-=3;if(canMelds(a,honors))return true;}
    if(!honors&&i+2<seg.length&&seg[i+1]>0&&seg[i+2]>0){var b=seg.slice();b[i]--;b[i+1]--;b[i+2]--;if(canMelds(b,honors))return true;}
    return false;
  }
  function stdWin(c){
    if(sum(c)!==14)return false;
    for(var p=0;p<34;p++){ if(c[p]<2)continue;
      var d=c.slice();d[p]-=2;var ok=true;
      for(var ci=0;ci<4;ci++){var b=CATBASE[ci],L=CATLEN[ci];
        if(!canMelds(d.slice(b,b+L),ci===3)){ok=false;break;}}
      if(ok)return true;
    }
    return false;
  }
  /* 严格七对子：7 种不同牌各 2 张（4 张同牌不算两对） */
  function chiitoiWin(c){
    var s=0,t2=0;
    for(var t=0;t<34;t++){ s+=c[t]; if(c[t]===2)t2++; else if(c[t]!==0)return false; }
    return s===14&&t2===7;
  }
  /* 国士无双：14 张且 13 种幺九字牌齐全（其中一种 2 张） */
  function kokushiWin(c){
    if(sum(c)!==14)return false;
    for(var t=0;t<34;t++) if(c[t]>0&&KOK.indexOf(t)<0) return false;
    for(var i=0;i<KOK.length;i++) if(c[KOK[i]]<1) return false;
    return true;
  }
  function win14(c){return stdWin(c)||chiitoiWin(c)||kokushiWin(c);}
  function waits13(c){
    var out=[];
    for(var t=0;t<34;t++){ if(c[t]>=4)continue; var d=c.slice(); d[t]++; if(win14(d))out.push(t); }
    return out;
  }
  function maskOf(w){var m=0;for(var i=0;i<w.length;i++)m+=Math.pow(2,w[i]);return m;}
  return {sum:sum,canMelds:canMelds,stdWin:stdWin,chiitoiWin:chiitoiWin,kokushiWin:kokushiWin,
          win14:win14,waits13:waits13,maskOf:maskOf,NAMES:NAMES};
})();
/* ===== 牌面图片（内联 base64，离线可用）与策略表（由 plan_k4_FINAL.json 生成） ===== */
__TILES__
var STRATEGY = __TABLE__;
/* 反向表：有序码 -> Wmask */
var CODE2MASK = (function(){
  var m={};
  for(var k in STRATEGY){ var cs=STRATEGY[k]; for(var i=0;i<cs.length;i++){ m[cs[i].join(",")]=Number(k); } }
  return m;
})();
var MJX = (function(){
  function contains(c,code){ var need={}; for(var i=0;i<code.length;i++){need[code[i]]=(need[code[i]]||0)+1;}
    for(var t in need){ if(c[t]<need[t]) return false; } return true; }
  /* A 的摆放：把一条 ⊆ H 的码放在最左 4 位（按码的顺序），其余按花色数字固定排布 */
  function encode(c){
    var w=MJ.waits13(c); if(!w.length) return null;
    var cs=STRATEGY[String(MJ.maskOf(w))]; if(!cs) return null;
    for(var i=0;i<cs.length;i++){ if(contains(c,cs[i])){
      var rest=c.slice(), out=cs[i].slice();
      for(var j=0;j<cs[i].length;j++) rest[cs[i][j]]--;
      for(var t=0;t<34;t++) for(var n=0;n<rest[t];n++) out.push(t);
      return {order:out, code:cs[i].slice(), waits:w};
    }}
    return null;
  }
  function decode(flipped){ var m=CODE2MASK[flipped.join(",")]; if(m===undefined) return null;
    var w=[]; for(var t=0;t<34;t++) if(Math.floor(m/Math.pow(2,t))%2===1) w.push(t); return w; }
  return {contains:contains,encode:encode,decode:decode};
})();
/* ===== 演示/UI ===== */
(function(){
  var $=function(id){return document.getElementById(id);};
  function tileLabel(t){
    var nm=MJ.NAMES[t];
    if(t<27) return nm[0];
    return {27:"東",28:"南",29:"西",30:"北",31:"白",32:"發",33:"中"}[t];
  }
  function tileClass(t){ return t<9?"m":t<18?"p":t<27?"s":"z"; }
  function tileEl(t,cls){
    var d=document.createElement("div");
    cls=cls||"";
    d.className="tile "+cls+" "+tileClass(t);
    var hi=/code|flip|emb/.test(cls);
    var img=document.createElement("img");
    img.src=(hi?TILE_SRC_EMB:TILE_SRC)[t];
    img.alt=tileLabel(t); img.title=MJ.NAMES[t]; img.draggable=false;
    img.onerror=function(){ this.style.display="none"; d.textContent=tileLabel(t); };
    d.appendChild(img);
    d.title=MJ.NAMES[t];
    return d;
  }
  function renderRow(el,tiles,extraCls){
    el.innerHTML="";
    tiles.forEach(function(t,i){ el.appendChild(tileEl(t, i<4?extraCls:"")); });
  }
  /* 把一手牌渲染到指定区域: ids={rowA,rowB,waits,info} */
  function renderTo(ids,c){
    var enc=MJX.encode(c);
    var w=enc?enc.waits:MJ.waits13(c);
    var wTxt=w.map(function(t){return MJ.NAMES[t];}).join(" ");
    if(!enc){
      renderRow($(ids.rowA),[],""); renderRow($(ids.rowB),[],"");
      $(ids.waits).innerHTML = w.length? ("真实听牌：<b>"+wTxt+"</b>（策略表中没有 ⊆ 本手的码）") : "未听牌（策略表只覆盖听牌手牌）";
      $(ids.info).textContent = "";
      refreshPalette(c);
      return {ok:false,waits:w};
    }
    renderRow($(ids.rowA),enc.order,"code");
    renderRow($(ids.rowB),enc.code,"flip");
    $(ids.waits).innerHTML = "查表得到的听牌：<b>"+wTxt+"</b>（共 "+w.length+" 种）";
    $(ids.info).textContent = "A：最左 4 张 = 有序码 ["+enc.code.map(function(t){return MJ.NAMES[t];}).join(",")+"]；B 翻开这 4 张 → 查表得到上述听牌。";
    refreshPalette(c);
    return {ok:true,waits:w};
  }
  /* ① 随机听牌手牌：反复采样直到听牌 */
  function randomHand(){
    for(var iter=0;iter<200000;iter++){
      var c=new Array(34).fill(0), n=0;
      while(n<13){ var t=Math.floor(Math.random()*34); if(c[t]<4){c[t]++;n++;} }
      if(MJ.waits13(c).length) return c;
    }
    // 兜底：构造式（4 面子 + 雀头 去一张）
    var melds=[],c=new Array(34).fill(0);
    for(var s=0;s<3;s++) for(var i=0;i<7;i++) melds.push([s*9+i,s*9+i+1,s*9+i+2]);
    for(var s2=0;s2<3;s2++) for(var i2=0;i2<9;i2++) melds.push([s2*9+i2,s2*9+i2,s2*9+i2]);
    for(var h=0;h<7;h++) melds.push([27+h,27+h,27+h]);
    for(var k=0;k<2000;k++){
      c=new Array(34).fill(0);
      for(var m=0;m<4;m++){ var M=melds[Math.floor(Math.random()*melds.length)]; M.forEach(function(t){c[t]++;}); }
      var p=Math.floor(Math.random()*34); c[p]+=2;
      var bad=false; for(var t2=0;t2<34;t2++) if(c[t2]>4) bad=true;
      if(bad) continue;
      var cands=[]; for(var t3=0;t3<34;t3++) if(c[t3]>0) cands.push(t3);
      c[cands[Math.floor(Math.random()*cands.length)]]--;
      if(MJ.waits13(c).length) return c;
    }
    return c;
  }
  /* ⑵ 文本解析 */
  function parseText(s,msgEl){
    s=(s||"").trim().toLowerCase().replace(/[^0-9mpsz]/g,"");
    var c=new Array(34).fill(0), buf=[];
    var suitMap={m:0,p:1,s:2,z:3};
    for(var i=0;i<s.length;i++){
      var ch=s[i];
      if(ch>="1"&&ch<="9"){ buf.push(Number(ch)); }
      else if(suitMap[ch]!==undefined){
        var ci=suitMap[ch], lim=(ci===3?7:9);
        for(var j=0;j<buf.length;j++){
          var num=buf[j];
          if(num<1||num>lim){ msgEl.textContent="错误：字牌只有 1z..7z（"+num+ch+" 越界）"; msgEl.className="msg bad"; return null; }
          c[CATBASE_[ci]+num-1]++;
        }
        buf=[];
      } else { msgEl.textContent="错误：非法字符 "+ch; msgEl.className="msg bad"; return null; }
    }
    if(buf.length){ msgEl.textContent="错误：结尾数字缺少花色后缀（m/p/s/z）"; msgEl.className="msg bad"; return null; }
    var n=0; for(var t=0;t<34;t++){ if(c[t]>4){ msgEl.textContent="错误："+MJ.NAMES[t]+" 超过 4 张"; msgEl.className="msg bad"; return null; } n+=c[t]; }
    if(n!==13){ msgEl.textContent="错误：共 "+n+" 张，需要 13 张"; msgEl.className="msg bad"; return null; }
    msgEl.textContent="OK：13 张，合法"; msgEl.className="msg good";
    return c;
  }
  var CATBASE_=[0,9,18,27];
  /* 调色板 */
  function buildPalette(){
    var p=$("palette"); p.innerHTML="";
    for(var t=0;t<34;t++){
      var d=tileEl(t,"small pick"); d.setAttribute("data-t",t);
      d.onclick=function(){ var t=Number(this.getAttribute("data-t"));
        var c=parseText($("custom").value,$("customMsg")); if(!c) c=new Array(34).fill(0);
        var n=0; for(var k=0;k<34;k++)n+=c[k];
        if(c[t]>=4){$("customMsg").textContent="该牌已 4 张";$("customMsg").className="msg bad";return;}
        if(n>=13){$("customMsg").textContent="已满 13 张，请先清空";$("customMsg").className="msg bad";return;}
        c[t]++; $("custom").value=toText(c); applyCustom();
      };
      p.appendChild(d);
    }
  }
  function toText(c){
    var out="";
    ["m","p","s","z"].forEach(function(su,ci){
      var lim=(ci===3?7:9), run="";
      for(var i=0;i<lim;i++){ var n=c[CATBASE_[ci]+i]; for(var k=0;k<n;k++) run+=(i+1); }
      if(run) out+=run+su;
    });
    return out;
  }
  function applyCustom(){
    var c=parseText($("custom").value,$("customMsg"));
    if(!c){ $("rowC").innerHTML=""; $("customWaits").innerHTML=""; return; }
    $("rowC").innerHTML="";
    for(var t=0;t<34;t++) for(var k=0;k<c[t];k++) $("rowC").appendChild(tileEl(t,"small"));
    var w=MJ.waits13(c);
    $("customWaits").innerHTML = w.length? ("真实听牌：<b>"+w.map(function(t){return MJ.NAMES[t];}).join(" ")+"</b>") : "未听牌";
    renderTo({rowA:"rowA2",rowB:"rowB2",waits:"customLookup",info:"customInfo"},c);
    refreshPalette(c);
  }
  function refreshPalette(c){
    var kids=$("palette").children;
    for(var i=0;i<kids.length;i++){ var t=Number(kids[i].getAttribute("data-t"));
      kids[i].className="tile small pick "+tileClass(t)+(c[t]>=4?" dis":""); }
  }
  /* ⑤ 自测 100 次 */
  function selfTest(n,logEl,msgEl){
    var bad=[], lines=[];
    for(var i=0;i<n;i++){
      var c=randomHand(); var trueW=MJ.waits13(c);
      if(!trueW.length){ bad.push({hand:toText(c),why:"非听牌(采样问题)"}); continue; }
      var enc=MJX.encode(c);
      if(!enc){ bad.push({hand:toText(c),why:"该类码表里没有 ⊆ 手牌的码"}); continue; }
      var flipped=enc.order.slice(0,4);
      var dec=MJX.decode(flipped);
      var key=function(w){return w.slice().sort(function(a,b){return a-b;}).join(",");};
      if(dec===null||key(dec)!==key(trueW)) bad.push({hand:toText(c),flipped:flipped.join(","),got:dec?dec.join(","):"null",want:trueW.join(",")});
    }
    if(!bad.length){
      msgEl.textContent="PASS（"+n+"/"+n+"）"; msgEl.className="msg good";
      logEl.textContent="自测 "+n+" 次：全部通过 ✅\\n判定：翻最左 4 张 → 查表听牌 == 真实听牌。";
    } else {
      msgEl.textContent="FAIL（"+(n-bad.length)+"/"+n+"）"; msgEl.className="msg bad";
      logEl.textContent="自测 "+n+" 次，失败 "+bad.length+" 个。前 3 个反例：\\n"+JSON.stringify(bad.slice(0,3),null,2);
    }
  }
  $("btnRandom").onclick=function(){ renderTo({rowA:"rowA",rowB:"rowB",waits:"waitsOut",info:"infoOut"},randomHand()); };
  $("btnApply").onclick=applyCustom;
  $("btnClear").onclick=function(){ $("custom").value=""; $("customMsg").textContent=""; applyCustom(); };
  $("btnSelfTest").onclick=function(){ selfTest(100,$("log"),$("selfTestMsg")); };
  buildPalette();
  // 初始示例
  (function(){ var c=parseText($("custom").value,$("customMsg")); if(c){ $("rowC").innerHTML=""; for(var t=0;t<34;t++) for(var k=0;k<c[t];k++) $("rowC").appendChild(tileEl(t,"small"));
      refreshPalette(c); var w=MJ.waits13(c); $("customWaits").innerHTML=w.length?("真实听牌：<b>"+w.map(function(t){return MJ.NAMES[t];}).join(" ")+"</b>"):"未听牌";
      renderTo({rowA:"rowA2",rowB:"rowB2",waits:"customLookup",info:"customInfo"},c); } })();
  window.__MJX_TEST__={randomHand:randomHand,selfTest:function(n){var bad=[];for(var i=0;i<n;i++){var c=randomHand();var tw=MJ.waits13(c);var enc=MJX.encode(c);if(!enc){bad.push([toText(c),"no-code"]);continue;}
    var dec=MJX.decode(enc.order.slice(0,4));var k=function(w){return w.slice().sort(function(a,b){return a-b;}).join(",");};
    if(dec===null||k(dec)!==k(tw))bad.push([toText(c),enc.order.slice(0,4).join(","),dec?dec.join(","):"null",tw.join(",")]);}
    return {n:n,bad:bad};},toText:toText,waitsOf:function(c){return MJ.waits13(c);},encode:MJX.encode};
})();
</script>
</body>
</html>
"""
os.makedirs(HERE, exist_ok=True)
open(os.path.join(HERE, "mahjong_demo.html"), "w", encoding="utf-8").write(
    HTML.replace("__TILES__", JS_TILES).replace("__TABLE__", tbl))
print("wrote web/mahjong_demo.html", os.path.getsize(os.path.join(HERE, "mahjong_demo.html")), "bytes")
