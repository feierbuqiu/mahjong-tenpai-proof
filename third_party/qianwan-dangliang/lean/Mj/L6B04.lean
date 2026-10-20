/- L6 第 4 批（20,000 块）内核检查：块级语义，失败块须为 0 -/
import Mj.L6Index

set_option maxHeartbeats 0

namespace Mj

/-- 第 4 批：480,024 个 (X1,X2) 单元，期望 (块数,失败块,单元数,失败单元) = (20000, 0, 480024, 0) -/
theorem l6_batch04_eq : batchAt 4 = (20000, 0, 480024, 0) := by native_decide

end Mj
