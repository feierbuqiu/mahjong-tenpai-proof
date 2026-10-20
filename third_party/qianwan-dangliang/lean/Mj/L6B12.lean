/- L6 第 12 批（20,000 块）内核检查：块级语义，失败块须为 0 -/
import Mj.L6Index

set_option maxHeartbeats 0

namespace Mj

/-- 第 12 批：213,877 个 (X1,X2) 单元，期望 (块数,失败块,单元数,失败单元) = (20000, 0, 213877, 0) -/
theorem l6_batch12_eq : batchAt 12 = (20000, 0, 213877, 0) := by native_decide

end Mj
