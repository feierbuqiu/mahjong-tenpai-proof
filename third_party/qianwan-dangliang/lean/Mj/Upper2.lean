/-
  Mj.Upper2 —— L6：II 型单元（5,402,697 个）在 Lean 内验证

  ===== 本轮（task-16 第一步 + 第二步雏形）已完成的部分 =====
  1) profile 谓词：canMelds / pdVec / wpOf / vOf / oddCount / otOf / a2Of / o2Of + iiKey
     （与 work/strategy/table_lib.x_profile 去掉 Wp 后的 6 元组 (V,pd,odd,ot,a2,o2) 一致）。
  2) **Lean 内枚举**：enumX len size = 「计数和 = size、每张 ≤ 4」的全部向量；aggOf c s 把
     (c,s) 的向量按 profile 聚合成 (keyEnc, |xs|, ΣencX) 并与 Data2 中 Python 写入的 profTable 比较
     ⇒ **profTableOk = true（native_decide）**：16 个 (c,s) 组、2,469 个 profile 全部一致
     （Python 侧独立复核：2,469 键 vs PROFII_D 的 xs 逐条对拍，0 不一致）。
  3) 块级覆盖检查（雏形）：decRec 解码 309,144 个块记录；iiBlockCovered 对每对 (X1,X2) 检查
     是否存在本类码 ⊆ X1⊎X2（严格单码判据，码按 c1/c2 过滤 + any 早停）。
     xs1/xs2 由 profile 查表得到（xsAll 是 CAF，每个 (c,s) 只枚举/分组一次）。

  ===== 已实测（子集）=====
  * 前 1,000 块：18,336 单元，失败块 0
  * 前 20,000 块：486,754 单元，失败块 **20**（失败单元 21）
    —— Python 独立复核（work/lean/probe10.py）得到**完全相同**的 20/21，
       即这 20 个块确实没有单条通用码（与 I 型 169 个反例同源），
       需用「多码/块级 DFS」语义才能覆盖（verifier 的 block_coverage_exact.py 报 II_uncovered = 0）。
  * 全量 5,402,697 单元**尚未在 Lean 内跑**；剩余 289,144 块 / 4,915,943 单元仍未检查。

  ===== 缺口 / 下一步 =====
  a) 把 iiBlockCovered 从「严格单码」升级为真正的块级语义（对每个 F 的多码/DFS 判定），
     才能让那 20 个块（估计全量几十~百余块）通过；
  b) 全量跑：把 checkBlocks 分块（每块 20k）并用 IO 计时输出，预计全量 ≈ 2–5 分钟
     （依据：本轮 3 组子集共 613k 单元的求值在 Mj.Upper2 的 21s 编译内完成）；
  c) 完成后即可删除 Mj/Upper.lean 里的 assumption iiUnitsComplete（用 iiBlocksAllCovered 取代）。
-/

import Mj.Basic
import Mj.Data
import Mj.Data2

set_option maxHeartbeats 0

namespace Mj

def catLen (c : Nat) : Nat := if c < 3 then 9 else 7
def catBase (c : Nat) : Nat := if c < 3 then c * 9 else 27
def tileCat (t : Nat) : Nat := if t < 27 then t / 9 else 3
def tilePos (t : Nat) : Nat := if t < 27 then t % 9 else t - 27

/-! ## profile 谓词（对齐 table_lib.x_profile） -/

def firstNz : List Nat → Nat → Option Nat
  | [], _ => none
  | x :: xs, i => if x > 0 then some i else firstNz xs (i + 1)

def canMelds : Bool → Nat → List Nat → Bool
  | _, 0, v => v.all (fun x => x == 0)
  | honors, fuel + 1, v =>
    match firstNz v 0 with
    | none => true
    | some i =>
      let c := v.getD i 0
      (decide (c ≥ 3) && canMelds honors fuel (v.set i (c - 3))) ||
      (if honors then false
       else if i + 2 < v.length && v.getD (i + 1) 0 > 0 && v.getD (i + 2) 0 > 0 then
         canMelds honors fuel
           (((v.set i (c - 1)).set (i + 1) (v.getD (i + 1) 0 - 1)).set (i + 2) (v.getD (i + 2) 0 - 1))
       else false)

def meldsOk (c : Nat) (v : List Nat) : Bool := canMelds (c == 3) (v.foldl (fun a x => a + x) 0) v

def pdVec (c : Nat) (v : List Nat) : Bool :=
  (List.range v.length).any (fun p => decide (v.getD p 0 ≥ 2) && meldsOk c (v.set p (v.getD p 0 - 2)))

def wpOf (c : Nat) (X : List Nat) : Nat :=
  (List.range X.length).foldl (fun acc t =>
    if X.getD t 0 < 4 && pdVec c (X.set t (X.getD t 0 + 1)) then acc ||| (1 <<< (catBase c + t)) else acc) 0

def vOf (c : Nat) (X : List Nat) : Nat :=
  (List.range X.length).foldl (fun acc t =>
    if X.getD t 0 < 4 && meldsOk c (X.set t (X.getD t 0 + 1)) then acc ||| (1 <<< (catBase c + t)) else acc) 0

def oddCount (X : List Nat) : Nat := X.foldl (fun a x => a + x % 2) 0

def otOf (c : Nat) (X : List Nat) : Option Nat :=
  let idxs := (List.range X.length).filter (fun i => X.getD i 0 % 2 == 1)
  if idxs.length == 1 then some (catBase c + idxs.headD 0) else none

def a2Of (X : List Nat) : Bool := X.all (fun x => x == 0 || x == 2)

def o2Of (X : List Nat) : Bool :=
  X.all (fun x => x == 0 || x == 1 || x == 2) && (X.filter (fun x => x == 1)).length == 1

def iiKey (c : Nat) (X : List Nat) : ProfKey :=
  { V := vOf c X, pd := pdVec c X, odd := oddCount X, ot := otOf c X, a2 := a2Of X, o2 := o2Of X }

def encX (X : List Nat) : Nat :=
  (List.range X.length).foldl (fun acc i => acc + X.getD i 0 * 5 ^ i) 0

def keyEnc (k : ProfKey) : Nat :=
  k.V + (if k.pd then 1 else 0) * 2 ^ 34 + k.odd * 2 ^ 35 +
  (match k.ot with | none => 34 | some t => t) * 2 ^ 39 +
  (if k.a2 then 1 else 0) * 2 ^ 45 + (if k.o2 then 1 else 0) * 2 ^ 46

/-! ## Lean 内枚举 -/

def enumGo : Nat → Nat → List Nat → List (List Nat)
  | 0, rem, acc => if rem == 0 then [acc.reverse] else []
  | fuel + 1, rem, acc =>
    (List.range (min 4 rem + 1)).flatMap (fun k => enumGo fuel (rem - k) (k :: acc))

def enumX (len size : Nat) : List (List Nat) := enumGo len size []

def ins3 (x : Nat × Nat × Nat) : List (Nat × Nat × Nat) → List (Nat × Nat × Nat)
  | [] => [x]
  | y :: ys => if decide (x.1 ≤ y.1) then x :: y :: ys else y :: ins3 x ys

def isort3 (xs : List (Nat × Nat × Nat)) : List (Nat × Nat × Nat) :=
  xs.foldl (fun acc x => ins3 x acc) []

/-- (c,s) 的聚合表：(keyEnc, |xs|, ΣencX) 升序 -/
def aggOf (c s : Nat) : List (Nat × Nat × Nat) :=
  let m : Std.HashMap Nat (Nat × Nat) :=
    (enumX (catLen c) s).foldl (fun m X =>
      let ke := keyEnc (iiKey c X)
      match m.get? ke with
      | some e => m.insert ke (e.1 + 1, e.2 + encX X)
      | none => m.insert ke (1, encX X)) {}
  isort3 (m.toList.map (fun (ke, e) => (ke, e.1, e.2)))

def aggMatches (cs : Nat × Nat) (infos : List ProfInfo) : Bool :=
  aggOf cs.1 cs.2 == infos.map (fun i => (keyEnc i.key, i.nXs, i.hXs))

/-- **自检**：Lean 枚举 + profile 分组，与 Python 写入的 profTable 逐条一致 -/
def profTableOk : Bool := profTable.all (fun t => aggMatches t.1 t.2)

theorem profTableOk_true : profTableOk = true := by native_decide

/-! ## 第二部分雏形：块级覆盖 -/

/-- (c,s) 的 profile 列表 -/
def profOf (c s : Nat) : List ProfInfo :=
  match profTable.find? (fun t => t.1 == (c, s)) with
  | some t => t.2
  | none => []

def keyOf (c s idx : Nat) : ProfKey :=
  match (profOf c s)[idx]? with
  | some i => i.key
  | none => { V := 0, pd := false, odd := 0, ot := none, a2 := false, o2 := false }

/-- 把 X 追加到 keyEnc 对应的桶 -/
def addTo (m : Std.HashMap Nat (List (List Nat))) (ke : Nat) (X : List Nat) :
    Std.HashMap Nat (List (List Nat)) :=
  match m.get? ke with
  | some l => m.insert ke (l ++ [X])
  | none => m.insert ke [X]

/-- 每个 (c,s) 的 keyEnc -> xs 映射（CAF，只算一次） -/
def xsMapOf (c s : Nat) : Std.HashMap Nat (List (List Nat)) :=
  (enumX (catLen c) s).foldl (fun m X => addTo m (keyEnc (iiKey c X)) X) {}

def xsAll : List (Std.HashMap Nat (List (List Nat))) :=
  profTable.map (fun t => xsMapOf t.1.1 t.1.2)

def xsLookup (c s ke : Nat) : List (List Nat) :=
  match xsAll[(profTable.findIdx? (fun t => t.1 == (c, s))).getD 0]? with
  | some m => m.getD ke []
  | none => []

def codesOfIdx (i : Nat) : List (List Nat) := (planData.getD i ([], [])).2

/-- 码 c 是否只落在 c1/c2 两门内 -/
def codeFitsCats (c : List Nat) (c1 c2 : Nat) : Bool :=
  c.all (fun t => tileCat t == c1 || tileCat t == c2)

/-- 码在类别 cat 内的需求表 [(局部位置, 需要张数)] -/
def reqOf (c : List Nat) (cat : Nat) : List (Nat × Nat) :=
  (List.range 34).filterMap (fun t =>
    if tileCat t == cat && c.count t > 0 then some (tilePos t, c.count t) else none)

def reqOk (reqs : List (Nat × Nat)) (X : List Nat) : Bool :=
  reqs.all (fun r => decide (X.getD r.1 0 ≥ r.2))

/-- 单元 (X1 in c1, X2 in c2) 是否被 codes 中某条码覆盖 -/
def unitCovered (codes : List (List Nat)) (c1 c2 : Nat) (X1 X2 : List Nat) : Bool :=
  codes.any (fun c => reqOk (reqOf c c1) X1 && reqOk (reqOf c c2) X2)

/-- 解码块记录：rec = classIdx*2^25 + comboIdx*2^18 + k1idx*2^9 + k2idx -/
def decRec (rec : Nat) : Nat × Nat × Nat × Nat × Nat × Nat × Nat :=
  let classIdx := rec / (1 <<< 25)
  let r1 := rec % (1 <<< 25)
  let comboIdx := r1 / (1 <<< 18)
  let r2 := r1 % (1 <<< 18)
  let k1idx := r2 / (1 <<< 9)
  let k2idx := r2 % (1 <<< 9)
  match combos[comboIdx]? with
  | some (c1, s1, c2, s2) => (classIdx, c1, s1, k1idx, c2, s2, k2idx)
  | none => (0, 0, 0, 0, 0, 0, 0)

/-! ## 第二步升级：块级多码 / DFS 语义

严格单码判据（∃ 码 ⊆ A）对某些块不成立；真正的块级语义是：
对每个 (X1,X2) 与每个合法补牌 F（inert 类别中的面子并集，张数 = 13-s1-s2），
只要存在**某条**码 ⊆ A⊎F 即可（不同 F 可以用不同码）。
下面复用 3 bit/张 打包 + 早停 DFS（与 Mj/Upper.lean 的块级检查同构，这里因两门活性部而独立实现）。 -/

def packVec2 (A : List Nat) : Nat :=
  (List.range 34).foldl (fun acc i => acc + (A.getD i 0 <<< (3 * i))) 0

def packInCat2 (c : Nat) (v : List Nat) : Nat :=
  (List.range v.length).foldl (fun acc i => acc + (v.getD i 0 <<< (3 * (catBase c + i)))) 0

def codeReq2 (c : List Nat) : List (Nat × Nat) :=
  (List.range 34).filterMap (fun t => if c.count t == 0 then none else some (3 * t, c.count t))

def reqOk2 (r : Nat × Nat) (h : Nat) : Bool := decide (r.2 ≤ (h >>> r.1) &&& 7)

def codeInHand2 (cr : List (Nat × Nat)) (h : Nat) : Bool := cr.all (fun r => reqOk2 r h)

def catsOf2 (mask : Nat) : List Nat := (List.range 4).filter (fun c => mask.testBit c)

def blockCovAux2 (reqs : List (List (Nat × Nat))) (h : Nat) (rem : Nat) (cats : List Nat) : Bool :=
  if reqs.any (fun cr => codeInHand2 cr h) then true
  else
    match cats with
    | [] => decide (rem ≠ 0)
    | c :: rest =>
      let maxRest := 12 * rest.length
      (List.range (rem / 3 + 1)).all (fun k =>
        let s := 3 * k
        if decide (rem - s ≤ maxRest) then
          (fillOf c s).all (fun v => blockCovAux2 reqs (h + packInCat2 c v) (rem - s) rest)
        else true)

/-- (X1 in c1, X2 in c2) + 任意补牌 F 是否都被本类码覆盖（块级语义） -/
def pairBlockCovered (reqs : List (List (Nat × Nat))) (c1 c2 : Nat) (X1 X2 : List Nat)
    (m : Nat) : Bool :=
  let h := packInCat2 c1 X1 + packInCat2 c2 X2
  blockCovAux2 reqs h m (catsOf2 (15 - (1 <<< c1) - (1 <<< c2)))

/-- 单个块：返回 (单元对数, 失败单元数)

注意语义细节：严格单码检查（∃ 码 ⊆ X1⊎X2）只需看落在 c1/c2 两门内的码；
但块级 DFS 检查的是 ∃ 码 ⊆ X1⊎X2⊎F，其中 F 在 inert 类别里，
**码完全可能用到 inert 类别的牌** ⇒ DFS 必须用该类的**全部**码，不能只用在 c1/c2 内的。 -/
def blockStat (rec : Nat) : Nat × Nat :=
  let (classIdx, c1, s1, k1idx, c2, s2, k2idx) := decRec rec
  let xs1 := xsLookup c1 s1 (keyEnc (keyOf c1 s1 k1idx))
  let xs2 := xsLookup c2 s2 (keyEnc (keyOf c2 s2 k2idx))
  let allCodes := codesOfIdx classIdx
  let codesA := allCodes.filter (fun c => codeFitsCats c c1 c2)
  -- 需求表按**块**只算一次（否则每个 (码,单元) 对都要重扫 34 张牌）
  let reqsA := codesA.map codeReq2
  let reqsAll := allCodes.map codeReq2
  let m := 13 - s1 - s2
  xs1.foldl (fun (u, f) X1 =>
    let h1 := packInCat2 c1 X1
    xs2.foldl (fun (u, f) X2 =>
      let hA := h1 + packInCat2 c2 X2
      let ok :=
        if reqsA.any (fun cr => codeInHand2 cr hA) then true
        else blockCovAux2 reqsAll hA m (catsOf2 (15 - (1 <<< c1) - (1 <<< c2)))
      (u + 1, if ok then f else f + 1)) (u, f)) (0, 0)

/-- 一批块：返回 (块数, 失败块数, 单元数, 失败单元数) -/
def batchStat (recs : List Nat) : Nat × Nat × Nat × Nat :=
  recs.foldl (fun (nb, fb, nu, fu) rec =>
    let (u, f) := blockStat rec
    (nb + 1, if f == 0 then fb else fb + 1, nu + u, fu + f)) (0, 0, 0, 0)

/-- 一个 II 块在**块级语义**下是否被覆盖 -/
def iiBlockCovered (rec : Nat) : Bool :=
  let (u, f) := blockStat rec
  decide (u > 0) && decide (f == 0)

/-- 返回 (检查块数, 失败块数, 检查的单元对数) -/
def checkBlocks (recs : List Nat) : Nat × Nat × Nat :=
  recs.foldl (fun (n, bad, u) rec =>
    let (uu, ff) := blockStat rec
    (n + 1, if ff == 0 then bad else bad + 1, u + uu)) (0, 0, 0)


/-! ## 分批统计（供编译期求值 + DumpL6.lean 输出） -/

/-- 把列表按 n 切段 -/
def chunkBlocks (n : Nat) (xs : List Nat) : List (List Nat) :=
  let rec go (fuel : Nat) (ys : List Nat) : List (List Nat) :=
    match fuel with
    | 0 => []
    | f + 1 => if ys.isEmpty then [] else (ys.take n) :: go f (ys.drop n)
  go (xs.length / n + 2) xs

def l6BatchSize : Nat := 20000

def l6Batches : List (List Nat) := chunkBlocks l6BatchSize blocks

/-- 每批 (块数, 失败块数, 单元数, 失败单元数)（块级语义） -/
def l6BatchStats : List (Nat × Nat × Nat × Nat) := l6Batches.map batchStat

/-- 全量汇总 -/
def l6Total : Nat × Nat × Nat × Nat :=
  l6BatchStats.foldl (fun (a, b, c, d) (x, y, z, w) => (a + x, b + y, c + z, d + w)) (0, 0, 0, 0)

/-! ## 全量验证：与 Python 独立实现（work/lean/verify_l6.py，块级语义 + 全码 DFS）逐批对拍 -/

/-- 每批期望值 (块数, 失败块数, 单元数, 失败单元数)，20,000 块一批，共 16 批 -/
def l6Expected : List (Nat × Nat × Nat × Nat) :=
  [(20000, 0, 486754, 0), (20000, 0, 458759, 0), (20000, 0, 321558, 0), (20000, 0, 413262, 0),
   (20000, 0, 480024, 0), (20000, 0, 327443, 0), (20000, 0, 396347, 0), (20000, 0, 476835, 0),
   (20000, 0, 341394, 0), (20000, 0, 305029, 0), (20000, 0, 289353, 0), (20000, 0, 297797, 0),
   (20000, 0, 213877, 0), (20000, 0, 308619, 0), (20000, 0, 197866, 0), (9144, 0, 87780, 0)]

/-- **本次会话已完成**的 Lean 内核检查：前 2,000 块（50,935 单元）在块级语义下失败 0
    （该数字由 work/lean/verify_l6.py 独立算出，Lean 用 native_decide 复算并核对）。 -/
theorem l6Slice2000_eq : batchStat ((l6Batches.getD 0 []).take 2000) = (2000, 0, 50935, 0) := by
  native_decide

/- 未完成（本次会话 3 次尝试 28 min / 18 min / 8+ min，均被时间上限打断）：
     theorem l6BatchStats_eq : l6BatchStats = l6Expected := by native_decide
     theorem l6Total_eq : l6Total = (309144, 0, 5402697, 0) := by native_decide
   全量 309,144 块 / 5,402,697 单元的结果目前来自独立 Python 实现
   （work/lean/verify_l6.py，块级语义 + 全码 DFS，8 进程 93.9 s，0 失败）；
   Lean 内核的全量 native 求值仍是缺口。 -/


end Mj
