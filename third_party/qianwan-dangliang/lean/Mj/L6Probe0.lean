import Mj.Upper2

set_option maxHeartbeats 0

namespace Mj

/-- 探针：第 0 批（20,000 块 / 486,754 单元）在 Lean 内核里跑块级语义检查 -/
theorem l6_batch0_eq : batchStat (l6Batches.getD 0 []) = (20000, 0, 486754, 0) := by
  native_decide

end Mj
