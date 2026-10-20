const fs=require('fs');
const html=fs.readFileSync('web/mahjong_demo.html','utf8');
const m=html.match(/<script id="core">([\s\S]*?)<\/script>/);
if(!m){ console.log('ERROR: core script not found'); process.exit(2); }
function mk(){ const o={textContent:'',className:'',title:'',value:'',children:[],style:{},
  appendChild(c){this.children.push(c);return c;},setAttribute(){},getAttribute(){return '0';},onclick:null};
  let ih=''; Object.defineProperty(o,'innerHTML',{get(){return ih;},set(v){ih=v;this.children.length=0;}}); return o; }
const els={};
global.document={getElementById(id){return els[id]||(els[id]=mk());},createElement(){return mk();}};
global.window={};
try { eval(m[1]); } catch(e){ console.log('EVAL ERROR', e.message); process.exit(3); }
const T=global.window.__MJX_TEST__;
const doc=global.document;
const r=T.selfTest(100);
console.log('SELFTEST100 failures='+r.bad.length);
if(r.bad.length) console.log('first3='+JSON.stringify(r.bad.slice(0,3)));
const cases=JSON.parse(fs.readFileSync('web/_js_cases.json','utf8'));
let mism=0; const key=w=>w.slice().sort((a,b)=>a-b).join(',');
for(const cs of cases){ if(key(T.waitsOf(cs.c))!==key(cs.w)) mism++; }
console.log('PYCROSS cases='+cases.length+' mismatch='+mism);
function apply(s){ doc.getElementById('custom').value=s; doc.getElementById('btnApply').onclick();
  return {lookup:doc.getElementById('customLookup').innerHTML, trueW:doc.getElementById('customWaits').innerHTML,
          rowA:doc.getElementById('rowA2').children.length, rowB:doc.getElementById('rowB2').children.length,
          info:doc.getElementById('customInfo').textContent}; }
const a=apply('123m456p789s11z22z');
console.log('CUSTOM tenpai: lookup="'+a.lookup.replace(/<[^>]+>/g,'')+'" | trueWaits="'+a.trueW.replace(/<[^>]+>/g,'')+'" | rowA='+a.rowA+' rowB='+a.rowB);
console.log('ASSERT lookup-updated='+/查表得到的听牌/.test(a.lookup)+' A13='+(a.rowA===13)+' B4='+(a.rowB===4)+' info='+(a.info.length>0));
const b=apply('1m1m1m1m9m9m9m9m1p1p1p1p2p');
console.log('CUSTOM non-tenpai: lookup="'+b.lookup.replace(/<[^>]+>/g,'')+'" | trueWaits="'+b.trueW.replace(/<[^>]+>/g,'')+'" rowA='+b.rowA+' rowB='+b.rowB);
console.log('ASSERT non-tenpai-message='+/未听牌/.test(b.lookup));
const c=apply('1m1m1m2m3m4m5m6m7m8m9m9m9m');
console.log('CUSTOM 9-wait: lookup="'+c.lookup.replace(/<[^>]+>/g,'')+'"');
console.log('ASSERT 9-wait-lookup='+/查表得到的听牌/.test(c.lookup));
console.log('SELFTEST300 failures='+T.selfTest(300).bad.length);
