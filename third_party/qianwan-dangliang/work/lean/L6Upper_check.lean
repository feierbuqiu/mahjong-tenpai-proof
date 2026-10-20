import Mj.L6Index

set_option maxHeartbeats 0

namespace Mj

def iiUnitsCovered : Prop :=
  totalIdx.1 = nIIBlocks ∧ totalIdx.2.1 = 0 ∧
  totalIdx.2.2.1 = nIIUnitsTotal ∧ totalIdx.2.2.2 = 0

theorem iiUnitsCovered_true_of (h : totalIdx = (309144, 0, 5402697, 0)) : iiUnitsCovered := by
  unfold iiUnitsCovered
  rw [h]
  refine ⟨?_, ?_, ?_, ?_⟩ <;> decide

theorem iiBlockCovered_of_zero (rec : Nat)
    (hpos : 0 < (blockStat rec).1) (hzero : (blockStat rec).2 = 0) :
    iiBlockCovered rec = true := by
  obtain ⟨u, f⟩ := blockStat rec
  simp only [iiBlockCovered] at hpos hzero ⊢
  simp [hzero, decide_eq_true_eq, hpos]

end Mj
