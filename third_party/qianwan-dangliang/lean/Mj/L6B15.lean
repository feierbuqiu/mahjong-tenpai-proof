/- L6 第 15 批（9,144 块）内核检查：块级语义，失败块须为 0 -/
import Mj.L6Index

set_option maxHeartbeats 0

namespace Mj

/-- 第 15 批：87,780 个 (X1,X2) 单元，期望 (块数,失败块,单元数,失败单元) = (9144, 0, 87780, 0) -/
theorem l6_batch15_eq : batchAt 15 = (9144, 0, 87780, 0) := by native_decide

end Mj
