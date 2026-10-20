/-
  Mj.L6Upper —— L7：把 II 型 5,402,697 个单元的块级覆盖从 assumption 换成**内核定理**。

  依赖（Lead 所有，勿改）：
    * Mj.L6Index : batchAt i = batchStat (l6Batches.getD i [])，totalIdx = Σ_{i<16} batchAt i
    * Mj.L6B00..L6B15 : theorem l6_batchNN_eq : batchAt NN = (块数, 0, 单元数, 0)  := by native_decide
    * Mj.L6Total : theorem totalIdx_eq : totalIdx = (309144, 0, 5402697, 0)（16 条批陈述的合取 + 字面算术）

  检查语义 = Mj.Upper2 的块级语义 + 全码 DFS（strict 单码通道 + 多码/DFS 通道）。
-/
import Mj.L6Total

set_option maxHeartbeats 0

namespace Mj

/-- **II 型全量覆盖谓词**（由 batchAt 求和得到）：
    totalIdx = (块数, 失败块数, 单元数, 失败单元数)，要求
    * 覆盖全部 309,144 个 II 块（= Mj.Data2.nIIBlocks）；
    * 失败块数 = 0；失败单元数 = 0；
    * 检查的单元对数 = 5,402,697（= Mj.Data2.nIIUnitsTotal，由 Python 侧独立统计并已与 Lean 枚举对拍）。 -/
def iiUnitsCovered : Prop :=
  totalIdx.1 = nIIBlocks ∧ totalIdx.2.1 = 0 ∧
  totalIdx.2.2.1 = nIIUnitsTotal ∧ totalIdx.2.2.2 = 0

/-- **内核证明**：直接由 Mj.L6Total.totalIdx_eq 得到
    （后者 = 16 条 native_decide 批陈述的合取 + 别名表的字面算术；定理名以 Lead 的为准）。 -/
theorem iiUnitsCovered_true : iiUnitsCovered := by
  unfold iiUnitsCovered
  rw [totalIdx_eq]
  refine ⟨?_, ?_, ?_, ?_⟩ <;> decide

/-- 与逐块谓词的接口（可选）：失败单元数为 0 的无空单元块即 iiBlockCovered。 -/
theorem iiBlockCovered_of_zero (rec : Nat)
    (hpos : 0 < (blockStat rec).1) (hzero : (blockStat rec).2 = 0) :
    iiBlockCovered rec = true := by
  obtain ⟨u, f⟩ := blockStat rec
  simp only [iiBlockCovered] at hpos hzero ⊢
  simp [hzero, hpos]

end Mj
