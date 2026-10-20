import Mj.L6B00
import Mj.L6B01
import Mj.L6B02
import Mj.L6B03

set_option maxHeartbeats 0

namespace Mj

def t4 : Nat × Nat × Nat × Nat :=
  [0,1,2,3].foldl (fun acc i => add4 acc (batchAt i)) (0, 0, 0, 0)

theorem t4_eq : t4 = (80000, 0, 1680333, 0) := by
  simp only [t4, add4, List.foldl_cons, List.foldl_nil,
    l6_batch00_eq, l6_batch01_eq, l6_batch02_eq, l6_batch03_eq]

end Mj
