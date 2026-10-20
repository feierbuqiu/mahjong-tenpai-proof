import Mj.L6Index

set_option maxHeartbeats 0

namespace Mj

/-- mock：用字面值替代 16 个 native_decide 定理，检验合并证明的脚本形状 -/
def mockBatchAt : Nat → Nat × Nat × Nat × Nat
  | 0 => (20000, 0, 486754, 0)
  | 1 => (20000, 0, 458759, 0)
  | 2 => (20000, 0, 321558, 0)
  | 3 => (20000, 0, 413262, 0)
  | 4 => (20000, 0, 480024, 0)
  | 5 => (20000, 0, 327443, 0)
  | 6 => (20000, 0, 396347, 0)
  | 7 => (20000, 0, 476835, 0)
  | 8 => (20000, 0, 341394, 0)
  | 9 => (20000, 0, 305029, 0)
  | 10 => (20000, 0, 289353, 0)
  | 11 => (20000, 0, 297797, 0)
  | 12 => (20000, 0, 213877, 0)
  | 13 => (20000, 0, 308619, 0)
  | 14 => (20000, 0, 197866, 0)
  | 15 => (9144, 0, 87780, 0)
  | _ => (0, 0, 0, 0)

def mockTotal : Nat × Nat × Nat × Nat :=
  idx16.foldl (fun acc i => add4 acc (mockBatchAt i)) (0, 0, 0, 0)

theorem mockTotal_eq : mockTotal = (309144, 0, 5402697, 0) := by
  simp only [mockTotal, idx16, add4, List.foldl_cons, List.foldl_nil, mockBatchAt]
  first | rfl | decide | native_decide

end Mj
