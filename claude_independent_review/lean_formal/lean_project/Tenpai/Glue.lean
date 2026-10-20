import Tenpai.CheckSound2

/-! # Glue between hands and the enumerations of the checks -/

namespace Tenpai

/-! ## enumerations contain the category vectors of hands -/

theorem mem_vecsD (d : Nat) : ∀ npos rem u, u ∈ vecsD d npos rem ↔
    ∃ f : Nat → Nat, (∀ j < npos, f j ≤ d) ∧ sumF f npos = rem ∧ u = pkF f npos
  | 0, rem, u => by
    show u ∈ cond (Nat.beq rem 0) [0] [] ↔ _
    cases h : Nat.beq rem 0
    · have : rem ≠ 0 := fun e => by subst e; simp at h
      simp only [Bool.cond_false, List.not_mem_nil, false_iff]
      rintro ⟨f, -, hs, -⟩
      exact this (by rw [← hs]; rfl)
    · have : rem = 0 := Nat.eq_of_beq_eq_true h
      subst this
      simp only [Bool.cond_true, List.mem_singleton]
      constructor
      · rintro rfl; exact ⟨fun _ => 0, by simp, rfl, rfl⟩
      · rintro ⟨f, -, -, rfl⟩; rfl
  | npos + 1, rem, u => by
    show u ∈ List.flatMap (fun c => cond (Nat.ble c rem)
      ((vecsD d npos (Nat.sub rem c)).map (fun x => Nat.add c (Nat.mul 16 x))) []) (List.range (Nat.succ d)) ↔ _
    rw [List.mem_flatMap]
    constructor
    · rintro ⟨c, hc, hu⟩
      have hcd : c ≤ d := by rw [List.mem_range] at hc; omega
      cases hb : Nat.ble c rem
      · simp [hb] at hu
      · have hcr : c ≤ rem := Nat.le_of_ble_eq_true hb
        simp only [hb, Bool.cond_true, List.mem_map] at hu
        obtain ⟨x, hx, rfl⟩ := hu
        obtain ⟨g, hg, hgs, rfl⟩ := (mem_vecsD d npos (rem - c) x).mp hx
        refine ⟨fun j => if j = 0 then c else g (j - 1), ?_, ?_, ?_⟩
        · intro j hj
          by_cases h0 : j = 0
          · simp [h0, hcd]
          · simp only [h0, ite_false]; exact hg _ (by omega)
        · have : ∀ n, sumF (fun j => if j = 0 then c else g (j - 1)) (n + 1) = c + sumF g n := by
            intro n
            induction n with
            | zero => simp [sumF]
            | succ n ih => rw [sumF, ih, sumF]; simp; omega
          rw [this, hgs]; show c + (rem - c) = rem; omega
        · rw [pkF_cons]
          show c + 16 * pkF g npos = _
          simp
    · rintro ⟨f, hf, hs, rfl⟩
      refine ⟨f 0, List.mem_range.mpr (by have := hf 0 (by omega); omega), ?_⟩
      have hsum : sumF f (npos + 1) = f 0 + sumF (fun j => f (j + 1)) npos := by
        clear hs hf
        induction npos with
        | zero => simp [sumF]
        | succ n ih => rw [sumF, ih, sumF]; omega
      have hle : f 0 ≤ rem := by rw [← hs, hsum]; omega
      have hb : Nat.ble (f 0) rem = true := Nat.ble_eq.mpr hle
      simp only [hb, Bool.cond_true, List.mem_map]
      refine ⟨pkF (fun j => f (j + 1)) npos, ?_, ?_⟩
      · rw [mem_vecsD d npos]
        exact ⟨fun j => f (j + 1), fun j hj => hf _ (by omega), by rw [← hs, hsum]; show _ = f 0 + _ - f 0; omega, rfl⟩
      · rw [pkF_cons]; rfl

theorem cv_mem_vecs (H : Counts) (hH : ∀ s, H s ≤ 4) (k : Nat) :
    cvOf H k ∈ vecs (catLen k) (hsize H k) :=
  (mem_vecs _ _ _).mpr ⟨catF (extF H) k, fun j _ => catF_le4 H hH k j, rfl, rfl⟩

theorem cv_mem_vecsD (H : Counts) (d : Nat) (hH : ∀ s, H s ≤ d) (k : Nat) :
    cvOf H k ∈ vecsD d (catLen k) (hsize H k) :=
  (mem_vecsD d _ _ _).mpr ⟨catF (extF H) k, fun j _ => by
    simp only [catF, extF]; split
    · exact hH _
    · omega, rfl, rfl⟩

/-! ## small computed facts -/

theorem cM_zero : ∀ k < 4, cM k 0 = true := by decide

/-- a single tile `j` in an otherwise empty category waits only on itself (pair) -/
theorem cWP_single_tile : ∀ k < 4, ∀ j < catLen k, cWP k (16 ^ j) = 2 ^ j := by decide

/-! ## masks -/

theorem mask_eq_of {M1 M2 : Nat} (h1 : ∀ i, 34 ≤ i → M1.testBit i = false)
    (h2 : ∀ i, 34 ≤ i → M2.testBit i = false) (h : ∀ i < 34, (M1.testBit i = true ↔ M2.testBit i = true)) :
    M1 = M2 := by
  apply Nat.eq_of_testBit_eq
  intro i
  by_cases hi : i < 34
  · cases e1 : M1.testBit i <;> cases e2 : M2.testBit i <;> simp_all
  · rw [h1 i (by omega), h2 i (by omega)]

theorem wAll_high (H : Counts) (_hH : IsHand H) (i : Nat) (hi : 34 ≤ i) : (wAll (cvOf H)).testBit i = false := by
  unfold wAll
  rw [testBit_lor', testBit_lor', testBit_maskBelow, testBit_maskBelow]
  have : (wStd (cvOf H)).testBit i = false := by
    cases h : (wStd (cvOf H)).testBit i
    · rfl
    · exact absurd ((stdW_iff H i).mp h).1 (by omega)
  rw [this]
  simp [show ¬ i < 34 by omega]

theorem shift9_high (m x : Nat) (hx : x < 4) (hm : ∀ j, catLen x ≤ j → m.testBit j = false) (i : Nat) (hi : 34 ≤ i) :
    (Nat.shiftLeft m (Nat.mul 9 x)).testBit i = false := by
  rw [testBit_shift9]
  by_cases h9 : 9 * x ≤ i
  · rw [hm (i - 9 * x) (by unfold catLen; split <;> omega)]; simp
  · simp [h9]

theorem cWP_high (k v j : Nat) (hj : catLen k ≤ j) : (cWP k v).testBit j = false := by
  cases h : (cWP k v).testBit j
  · rfl
  · rw [testBit_cWP] at h; omega

theorem cWM_high (k v j : Nat) (hj : catLen k ≤ j) : (cWM k v).testBit j = false := by
  cases h : (cWM k v).testBit j
  · rfl
  · rw [testBit_cWM] at h; omega

/-! ## standard waits of a hand -/

theorem stdW_iff_standard (H : Counts) (hH : IsHand H) (t : Tile) :
    StdW H t.val ↔ H t < 4 ∧ IsStandard (addTile H t) := by
  have hfx : fld (cvOf H (t.val / 9)) (t.val % 9) = H t := fld_catPk H hH.2 t
  unfold StdW
  constructor
  · rintro ⟨-, h4, h⟩
    rw [hfx] at h4
    exact ⟨h4, (std_wait_iff H hH t h4).mpr h⟩
  · rintro ⟨h4, h⟩
    exact ⟨t.isLt, by rw [hfx]; exact h4, (std_wait_iff H hH t h4).mp h⟩

/-! ## seven-pairs shape -/

/-- `H` is six distinct pairs plus the single `z` -/
def Shaped7 (H : Counts) (z : Tile) : Prop :=
  H z = 1 ∧ (∀ s, s ≠ z → H s = 0 ∨ H s = 2) ∧ (List.finRange 34).countP (fun s => H s = 2) = 6

theorem countP_eq_total (p : Tile → Prop) [DecidablePred p] :
    (List.finRange 34).countP (fun s => p s) = total (fun s => if p s then 1 else 0) := by
  unfold total
  generalize List.finRange 34 = L
  induction L with
  | nil => rfl
  | cons a L ih =>
    rw [List.countP_cons, ih, List.map_cons, List.sum_cons]
    by_cases ha : p a <;> simp [ha] <;> omega

theorem sevenW_iff (H : Counts) (t : Tile) :
    (H t < 4 ∧ IsSevenPairs (addTile H t)) ↔ Shaped7 H t := by
  rw [isSevenPairs_iff]
  have hcnt : H t = 1 → (List.finRange 34).countP (fun s => addTile H t s = 2) =
      (List.finRange 34).countP (fun s => H s = 2) + 1 := by
    intro h1
    rw [countP_eq_total, countP_eq_total]
    have e : (fun s => if addTile H t s = 2 then 1 else 0) =
        fun s => (if H s = 2 then 1 else 0) + (if s = t then 1 else 0) := by
      funext s
      simp only [addTile]
      by_cases hs : s = t
      · subst hs; simp [h1]
      · simp [hs]
    rw [e, total_add, total_indicator]
  constructor
  · rintro ⟨h4, h02, hc⟩
    have h1 : H t = 1 := by have := h02 t; simp only [addTile, ite_true] at this; omega
    refine ⟨h1, fun s hs => ?_, ?_⟩
    · have := h02 s; simp only [addTile, hs, ite_false] at this; exact this
    · rw [hcnt h1] at hc; omega
  · rintro ⟨h1, h02, hc⟩
    refine ⟨by omega, fun s => ?_, by rw [hcnt h1, hc]⟩
    by_cases hs : s = t
    · subst hs; simp [addTile, h1]
    · simp only [addTile, hs, ite_false]; exact h02 s hs

theorem shaped7_unique (H : Counts) (z z' : Tile) (h : Shaped7 H z) (h' : Shaped7 H z') : z = z' :=
  Decidable.byContradiction fun hne => by
    have := h.2.1 z' (fun e => hne e.symm)
    have := h'.1
    omega

end Tenpai
