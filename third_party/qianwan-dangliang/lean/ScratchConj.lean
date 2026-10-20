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

/-- 不带任何重写：16 条批陈述的合取。语义上就是全量结论。 -/
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

end Mj
