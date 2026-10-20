/-
  Mj.L6Total —— 把 16 个批次的内核结论拼成**一条**关于 totalIdx 的全量定理（Lead）

  ⚠️ 实测教训（2026-09-18，两次 OOM 换来的）：
  * 用一条 simp only [totalIdx, idx16, ..., l6_batch00_eq, ... l6_batch15_eq] 合并 ⇒ 23 GB OOM；
  * 改成顺序 rw [l6_batch00_eq, ..., l6_batch15_eq] ⇒ 同样 25 GB OOM；
  * 原因：batchAt i 是 def，任何重写匹配/失败尝试都会 delta-展开成
    batchStat (l6Batches.getD i [])，进而求值 chunkBlocks（309,144 元素），反复构造巨项。
  * 实测对照：**不做任何重写**、只给出 16 条批陈述的合取 ⇒ 1 s / 76 MB。
  * 解法：给每批一个**不同 head 常量**的别名 b00..b15（定义上就是 batchAt k），
    重写规则的 LHS head 互不相同 ⇒ simp 判别树精确命中，不产生跨批展开尝试。

  结论链：l6_all_batches（16 条内核事实）+ totalIdxB_eq（别名表的字面算术）
          ⇒ totalIdx_eq（接回 L6Index 的 totalIdx 定义）。
-/
import Mj.L6B00
import Mj.L6B01
import Mj.L6B02
import Mj.L6B03
import Mj.L6B04
import Mj.L6B05
import Mj.L6B06
import Mj.L6B07
import Mj.L6B08
import Mj.L6B09
import Mj.L6B10
import Mj.L6B11
import Mj.L6B12
import Mj.L6B13
import Mj.L6B14
import Mj.L6B15

set_option maxHeartbeats 0

namespace Mj

/-- 16 条批陈述的合取：全量结论的「无重写」形式（内核验证，几乎零代价） -/
theorem l6_all_batches :
    batchAt 0 = (20000, 0, 486754, 0) ∧
    batchAt 1 = (20000, 0, 458759, 0) ∧
    batchAt 2 = (20000, 0, 321558, 0) ∧
    batchAt 3 = (20000, 0, 413262, 0) ∧
    batchAt 4 = (20000, 0, 480024, 0) ∧
    batchAt 5 = (20000, 0, 327443, 0) ∧
    batchAt 6 = (20000, 0, 396347, 0) ∧
    batchAt 7 = (20000, 0, 476835, 0) ∧
    batchAt 8 = (20000, 0, 341394, 0) ∧
    batchAt 9 = (20000, 0, 305029, 0) ∧
    batchAt 10 = (20000, 0, 289353, 0) ∧
    batchAt 11 = (20000, 0, 297797, 0) ∧
    batchAt 12 = (20000, 0, 213877, 0) ∧
    batchAt 13 = (20000, 0, 308619, 0) ∧
    batchAt 14 = (20000, 0, 197866, 0) ∧
    batchAt 15 = (9144, 0, 87780, 0) :=
  ⟨l6_batch00_eq, l6_batch01_eq, l6_batch02_eq, l6_batch03_eq, l6_batch04_eq, l6_batch05_eq, l6_batch06_eq, l6_batch07_eq, l6_batch08_eq, l6_batch09_eq, l6_batch10_eq, l6_batch11_eq, l6_batch12_eq, l6_batch13_eq, l6_batch14_eq, l6_batch15_eq⟩

/-! ## 别名（不同 head 常量）与字面总量 -/

/-- 第 0 批的别名（定义上等于 batchAt 0） -/
def b00 : Nat × Nat × Nat × Nat := batchAt 0

/-- 第 1 批的别名（定义上等于 batchAt 1） -/
def b01 : Nat × Nat × Nat × Nat := batchAt 1

/-- 第 2 批的别名（定义上等于 batchAt 2） -/
def b02 : Nat × Nat × Nat × Nat := batchAt 2

/-- 第 3 批的别名（定义上等于 batchAt 3） -/
def b03 : Nat × Nat × Nat × Nat := batchAt 3

/-- 第 4 批的别名（定义上等于 batchAt 4） -/
def b04 : Nat × Nat × Nat × Nat := batchAt 4

/-- 第 5 批的别名（定义上等于 batchAt 5） -/
def b05 : Nat × Nat × Nat × Nat := batchAt 5

/-- 第 6 批的别名（定义上等于 batchAt 6） -/
def b06 : Nat × Nat × Nat × Nat := batchAt 6

/-- 第 7 批的别名（定义上等于 batchAt 7） -/
def b07 : Nat × Nat × Nat × Nat := batchAt 7

/-- 第 8 批的别名（定义上等于 batchAt 8） -/
def b08 : Nat × Nat × Nat × Nat := batchAt 8

/-- 第 9 批的别名（定义上等于 batchAt 9） -/
def b09 : Nat × Nat × Nat × Nat := batchAt 9

/-- 第 10 批的别名（定义上等于 batchAt 10） -/
def b10 : Nat × Nat × Nat × Nat := batchAt 10

/-- 第 11 批的别名（定义上等于 batchAt 11） -/
def b11 : Nat × Nat × Nat × Nat := batchAt 11

/-- 第 12 批的别名（定义上等于 batchAt 12） -/
def b12 : Nat × Nat × Nat × Nat := batchAt 12

/-- 第 13 批的别名（定义上等于 batchAt 13） -/
def b13 : Nat × Nat × Nat × Nat := batchAt 13

/-- 第 14 批的别名（定义上等于 batchAt 14） -/
def b14 : Nat × Nat × Nat × Nat := batchAt 14

/-- 第 15 批的别名（定义上等于 batchAt 15） -/
def b15 : Nat × Nat × Nat × Nat := batchAt 15

def bAll : List (Nat × Nat × Nat × Nat) :=
  [b00, b01, b02, b03, b04, b05, b06, b07, b08, b09, b10, b11, b12, b13, b14, b15]

def totalIdxB : Nat × Nat × Nat × Nat := bAll.foldl add4 (0, 0, 0, 0)

/-- 别名表之和（纯字面算术，重写规则 head 互不相同） -/
theorem totalIdxB_eq : totalIdxB = (309144, 0, 5402697, 0) := by
  have h00 : b00 = (20000, 0, 486754, 0) := l6_batch00_eq
  have h01 : b01 = (20000, 0, 458759, 0) := l6_batch01_eq
  have h02 : b02 = (20000, 0, 321558, 0) := l6_batch02_eq
  have h03 : b03 = (20000, 0, 413262, 0) := l6_batch03_eq
  have h04 : b04 = (20000, 0, 480024, 0) := l6_batch04_eq
  have h05 : b05 = (20000, 0, 327443, 0) := l6_batch05_eq
  have h06 : b06 = (20000, 0, 396347, 0) := l6_batch06_eq
  have h07 : b07 = (20000, 0, 476835, 0) := l6_batch07_eq
  have h08 : b08 = (20000, 0, 341394, 0) := l6_batch08_eq
  have h09 : b09 = (20000, 0, 305029, 0) := l6_batch09_eq
  have h10 : b10 = (20000, 0, 289353, 0) := l6_batch10_eq
  have h11 : b11 = (20000, 0, 297797, 0) := l6_batch11_eq
  have h12 : b12 = (20000, 0, 213877, 0) := l6_batch12_eq
  have h13 : b13 = (20000, 0, 308619, 0) := l6_batch13_eq
  have h14 : b14 = (20000, 0, 197866, 0) := l6_batch14_eq
  have h15 : b15 = (9144, 0, 87780, 0) := l6_batch15_eq
  simp only [totalIdxB, bAll, add4, List.foldl_cons, List.foldl_nil,
    h00,
    h01,
    h02,
    h03,
    h04,
    h05,
    h06,
    h07,
    h08,
    h09,
    h10,
    h11,
    h12,
    h13,
    h14,
    h15]

/-- **全量定理**：16 批之和 = (块数 309144, 失败块 0, 单元 5402697, 失败单元 0) -/
theorem totalIdx_eq : totalIdx = (309144, 0, 5402697, 0) := by
  rw [← totalIdxB_eq]
  rfl

#print axioms totalIdx_eq

end Mj
