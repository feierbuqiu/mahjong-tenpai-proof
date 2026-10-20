/-
  Mj.Upper —— k=4 上界计划的可判定检查器（任务 L4，块级语义版）

  对象：work/verify/plan_k4_FINAL.json（2846 类 / 17,579 条 4 元码），数据由
  work/lean/gen_data.py 编译成 Mj/Data.lean（planData / iUnitData / fillOf / 计数常量）。

  检查项：
    (a) 每码长度 4；全部码全局唯一；
    (b) 每类至少 1 条码；
    (c) **块级覆盖语义**：一个来源块 = (活性部 A, 惰性类别集合 inert, 补牌张数 m)。
        该块被覆盖 ⟺ 对每一个由 inert 类别中的面子（刻子/顺子；字牌无顺子）拼成、
        总张数恰为 m 的补牌多重集 F，都存在本类码 c 使 计数(c) ≤ A + F。
        > 注意：|A| >= 4 时它蕴含「∃ c ⊆ A」；|A| = 1 的 tanki 块没有 c ⊆ A，
          必须靠补牌族 DFS（这正是 169 个严格反例的成因，见下）。

  === 结论 ===
  * structOk = true              —— (a)(b)，native_decide
  * iBlocksAllCovered = true     —— 全部 168,817 个 I 型单元的块级覆盖，native_decide
  * iUnitsAllStrict = false      —— 仅查「∃ c ⊆ A」的严格检查不通过（说明性结论）
  * iUnitFailures.length = 169   —— 反例个数（全部落在 34 个单张类的 tanki/size4 块）
  * iiUnitsCovered               —— 5,402,697 个 II 型单元的块级覆盖：**内核定理**
                                    （Mj.L6Upper.iiUnitsCovered_true，经 Mj.L6Total.l6TotalIdx_eq；
                                     L7 起本文件不再含任何 axiom）

  `#print axioms checkPlan_true` 现在只应列出 native_decide 的可信基
  （Lean.ofReduceBool / Lean.trustCompiler）与 propext，不再有自定义 assumption。
-/
import Mj.Basic
import Mj.Data
import Mj.L6Upper

namespace Mj

-- 注：tileCat / tilePos 已由 Mj.Upper2（经 Mj.L6Upper → Mj.L6Total 链）提供，
-- 本文件不再重复定义，避免与 Mj.Upper2 的同名常量冲突。

/-- 类别起始牌索引 -/
def catOff (c : Nat) : Nat := if c < 3 then c * 9 else 27

/-! ## 3 bit/张 的计数向量打包（每张 <= 4 < 8，加法不产生进位） -/

def packVec (A : List Nat) : Nat :=
  (List.range 34).foldl (fun acc i => acc + (A.getD i 0 <<< (3 * i))) 0

def packInCat (c : Nat) (v : List Nat) : Nat :=
  (List.range v.length).foldl (fun acc i => acc + (v.getD i 0 <<< (3 * (catOff c + i)))) 0

/-- 码 c 的需求表：[(bit 偏移, 需要张数)] -/
def codeReq (c : List Nat) : List (Nat × Nat) :=
  (List.range 34).filterMap (fun t => if c.count t == 0 then none else some (3 * t, c.count t))

def reqOkOne (r : Nat × Nat) (h : Nat) : Bool := decide (r.2 ≤ (h >>> r.1) &&& 7)

/-- 码（需求表）是否 ⊆ 手牌打包值 h -/
def codeInHand (cr : List (Nat × Nat)) (h : Nat) : Bool := cr.all (fun r => reqOkOne r h)

/-! ## I 型单元的编码解码（Data: u = cat*6^9 + Σ_i count_i*6^i） -/

def unitCat (u : Nat) : Nat := u / six9

def unitSize (u : Nat) : Nat :=
  (List.range 9).foldl (fun acc i => acc + (u / 6 ^ i) % 6) 0

/-- 单元对应活性部 A 的 3-bit 打包（A 全在 unitCat u 这一门内） -/
def unitHand (u : Nat) : Nat :=
  (List.range 9).foldl
    (fun acc i => acc + (((u / 6 ^ i) % 6) <<< (3 * (catOff (unitCat u) + i)))) 0

def catsOf (mask : Nat) : List Nat := (List.range 4).filter (fun c => mask.testBit c)

/-- 类键 -> 码表 -/
def codesOf (key : List Nat) : List (List Nat) :=
  match planData.find? (fun p => p.1 == key) with
  | some p => p.2
  | none => []

/-! ## 块级覆盖 DFS

reqs: 本类全部码的需求表；h: 当前部分手牌（A + 已选补牌）的打包值；
rem: 还需要补的张数；cats: 尚未处理的惰性类别。 -/

def blockCovAux (reqs : List (List (Nat × Nat))) (h : Nat) (rem : Nat) (cats : List Nat) : Bool :=
  if reqs.any (fun cr => codeInHand cr h) then true
  else
    match cats with
    | [] => decide (rem ≠ 0)
    | c :: rest =>
      let maxRest := 12 * rest.length
      (List.range (rem / 3 + 1)).all (fun k =>
        let s := 3 * k
        if decide (rem - s ≤ maxRest) then
          (fillOf c s).all (fun v => blockCovAux reqs (h + packInCat c v) (rem - s) rest)
        else true)

/-- 任务书要求的接口：块 (A, inertMask, m) 是否被 codes 覆盖 -/
def blockCovered (codes : List (List Nat)) (A : List Nat) (inertMask : Nat) (m : Nat) : Bool :=
  blockCovAux (codes.map codeReq) (packVec A) m (catsOf inertMask)

/-- I 型单元 u 的块级覆盖（惰性类别 = 除 unitCat u 外的全部门） -/
def unitBlockCovered (reqs : List (List (Nat × Nat))) (u : Nat) : Bool :=
  blockCovAux reqs (unitHand u) (13 - unitSize u) (catsOf (15 - (1 <<< unitCat u)))

/-- 严格（仅 ∃c ⊆ A）检查单个单元 -/
def unitStrictCovered (reqs : List (List (Nat × Nat))) (u : Nat) : Bool :=
  reqs.any (fun cr => codeInHand cr (unitHand u))

/-! ## (a)(b) 结构检查 -/

def codesLen4 : Bool := planData.all (fun p => p.2.all (fun c => c.length == 4))

def encCode (c : List Nat) : Nat := c.foldl (fun acc t => acc * 34 + t) 0

def allCodeNats : List Nat := planData.foldl (fun acc p => acc ++ p.2.map encCode) []

def insNat (x : Nat) : List Nat → List Nat
  | [] => [x]
  | y :: ys => if decide (x ≤ y) then x :: y :: ys else y :: insNat x ys

def isortNat (xs : List Nat) : List Nat := xs.foldl (fun acc x => insNat x acc) []

def noAdjEq : List Nat → Bool
  | [] => true
  | [_] => true
  | a :: b :: rest => (a != b) && noAdjEq (b :: rest)

def codesUnique : Bool := noAdjEq (isortNat allCodeNats)

def classesNonEmpty : Bool := planData.all (fun p => !p.2.isEmpty)

def structOk : Bool := codesLen4 && codesUnique && classesNonEmpty

theorem structOk_true : structOk = true := by native_decide

/-! ## (c) I 型：块级覆盖（全部 168,817 个单元） -/

def iBlocksAllCovered : Bool :=
  iUnitData.all (fun p =>
    let reqs := (codesOf p.1).map codeReq
    p.2.all (fun u => unitBlockCovered reqs u))

theorem iBlocksAllCovered_true : iBlocksAllCovered = true := by native_decide

/-! ## 说明性结论：严格判据 (∃c ⊆ A) 不通过，反例 169 个 -/

def iUnitsAllStrict : Bool :=
  iUnitData.all (fun p =>
    let reqs := (codesOf p.1).map codeReq
    p.2.all (fun u => unitStrictCovered reqs u))

theorem iUnitsAllStrict_false : iUnitsAllStrict = false := by native_decide

/-- 反例去重后的个数（169 个出现次数含两个块变体的重复；去重后 135） -/
theorem iUnitFailures_length : iUnitFailures.length = nUnitFailures := by native_decide

def iUnitsOkExcept : Bool :=
  iUnitData.all (fun p =>
    let reqs := (codesOf p.1).map codeReq
    p.2.all (fun u => if iUnitFailures.contains (p.1, u) then true else unitStrictCovered reqs u))

theorem iUnitsOkExcept_true : iUnitsOkExcept = true := by native_decide

def failuresAreReal : Bool :=
  iUnitFailures.all (fun q =>
    let reqs := (codesOf q.1).map codeReq
    (!unitStrictCovered reqs q.2) && iUnitData.any (fun p => p.1 == q.1 && p.2.contains q.2))

theorem failuresAreReal_true : failuresAreReal = true := by native_decide

/-! ## II 型：内核定理（L7 起不再有 assumption）

II 型单元 5,402,697 个（每个由 (X1,X2) 两个计数向量给出），按 309,144 个块展开，
其块级覆盖（strict 单码通道 + 多码/DFS 通道，语义见 Mj/Upper2.lean）由 16 个批次模块
Mj.L6B00..L6B15 各跑一次 native_decide，再由 Mj.L6Total.totalIdx_eq 汇成一条全量定理；
Mj.L6Upper.iiUnitsCovered_true 把它包装成覆盖谓词。
**原先的 axiom iiUnitsComplete / iiUnitsComplete_proof 已在 L7 删除。**
-/

/-! ## 汇总 -/

/-- Lean 内核可判定的部分：(a)(b) + I 型块级覆盖 + 反例为真 -/
def checkPlanComputable : Bool := structOk && iBlocksAllCovered && failuresAreReal

theorem checkPlanComputable_true : checkPlanComputable = true := by
  have h1 : structOk = true := structOk_true
  have h2 : iBlocksAllCovered = true := iBlocksAllCovered_true
  have h3 : failuresAreReal = true := failuresAreReal_true
  simp [checkPlanComputable, h1, h2, h3]

/-- 汇总：可判定部分通过，且 II 型全量覆盖成立（**内核定理**，非假设）。 -/
theorem checkPlan_true : checkPlanComputable = true ∧ iiUnitsCovered :=
  ⟨checkPlanComputable_true, iiUnitsCovered_true⟩

/-- 汇总定理（结论逐条列出；不再依赖任何 assumption） -/
theorem upper_k4 :
    structOk = true ∧ iBlocksAllCovered = true ∧ failuresAreReal = true ∧
    iUnitsAllStrict = false ∧ iiUnitsCovered :=
  ⟨structOk_true, iBlocksAllCovered_true, failuresAreReal_true, iUnitsAllStrict_false,
   iiUnitsCovered_true⟩

#print axioms checkPlan_true
#print axioms upper_k4
#print axioms iBlocksAllCovered_true
#print axioms structOk_true

end Mj
