/-
  Mj.L6Index —— L6 全量验证的**索引层**（task-16，Lead）

  动机：把 309,144 个 II 型块的检查拆成 16 个互相独立的批次模块
  （Mj.L6B00 .. Mj.L6B15），每个模块单独跑一次 native_decide，
  这样 Lake / 调度器可以并行编译，把原先"整块 native_decide 跑不完"
  的问题变成 16 个 ~257 s 的子问题；最后由 Mj.L6Total 用**廉价**的
  重写把 16 个结论拼成一条全量定理（拼接不重新求值）。

  定义与检查语义全部复用 Mj.Upper2（块级语义 + 全码 DFS）。
-/

import Mj.Upper2

set_option maxHeartbeats 0

namespace Mj

/-- 16 个批次的索引（字面表，避免依赖 List.range 的化简引理） -/
def idx16 : List Nat := [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]

/-- 四元组加法（core/Std 里 Nat×Nat×Nat×Nat 没有 Add 实例，显式定义以便内核化简） -/
def add4 : Nat × Nat × Nat × Nat → Nat × Nat × Nat × Nat → Nat × Nat × Nat × Nat
  | (a, b, c, d), (x, y, z, w) => (a + x, b + y, c + z, d + w)

/-- 第 i 批的 (块数, 失败块数, 单元数, 失败单元数) -/
def batchAt (i : Nat) : Nat × Nat × Nat × Nat := batchStat (l6Batches.getD i [])

/-- 16 批结果之和 -/
def totalIdx : Nat × Nat × Nat × Nat :=
  idx16.foldl (fun acc i => add4 acc (batchAt i)) (0, 0, 0, 0)

/- 注：关于 l6Batches.length = 16 这类需要 native 求值的事实放在 Mj/L6Bridge.lean（L8），
   避免 L6Index 里出现 native_decide 而拖慢 16 个批次模块的共同依赖。 -/

theorem l6_batchsize_ok : l6BatchSize = 20000 := by rfl

end Mj
