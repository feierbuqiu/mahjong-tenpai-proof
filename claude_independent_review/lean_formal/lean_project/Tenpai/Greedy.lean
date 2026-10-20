import Tenpai.Packed

/-!
# Correctness of the greedy meld test

A local count vector `w` (positions `0 … n-1`) splits into melds iff there are
`tr j` triplets and `sq j` sequences starting at each position `j`
(sequences only at `j < lim`) with
`w j = 3·tr j + sq j + sq (j-1) + sq (j-2)`.
The greedy `grW` decides this: at the lowest position the number of sequences can be
taken `< 3` (three equal sequences are three triplets), so it equals the remainder mod 3.
-/

namespace Tenpai

/-- tiles needed at position `i` by sequences started at `i-1` and `i-2` -/
def seqCov (sq : Nat → Nat) (i : Nat) : Nat :=
  (if 1 ≤ i then sq (i - 1) else 0) + (if 2 ≤ i then sq (i - 2) else 0)

/-- count form of a meld decomposition of `w` on positions `< n` -/
def LocalDec (w : Nat → Nat) (lim n : Nat) : Prop :=
  ∃ tr sq : Nat → Nat, (∀ i, sq i ≠ 0 → i < lim) ∧ ∀ i < n, w i = 3 * tr i + sq i + seqCov sq i

/-- pending demand at position `i ≥ j` when the greedy stands at `j` with state `(p0, p1)`
    and the sequences `sq` start at positions `≥ j` -/
def pend (j p0 p1 : Nat) (sq : Nat → Nat) (i : Nat) : Nat :=
  (if i = j then p0 else 0) + (if i = j + 1 then p1 else 0) +
  (if j + 1 ≤ i then sq (i - 1) else 0) + (if j + 2 ≤ i then sq (i - 2) else 0)

/-- the suffix invariant of the greedy -/
def SufDec (w : Nat → Nat) (lim n j p0 p1 : Nat) : Prop :=
  ∃ tr sq : Nat → Nat, (∀ i, sq i ≠ 0 → j ≤ i ∧ i < lim) ∧ (p0 ≠ 0 → j < n) ∧ (p1 ≠ 0 → j + 1 < n) ∧
    ∀ i, j ≤ i → i < n → w i = 3 * tr i + sq i + pend j p0 p1 sq i

/-- point update of a function -/
def upd (f : Nat → Nat) (j v : Nat) : Nat → Nat := fun i => if i = j then v else f i

@[simp] theorem upd_same (f : Nat → Nat) (j v : Nat) : upd f j v j = v := by simp [upd]
theorem upd_ne (f : Nat → Nat) {j i : Nat} (v : Nat) (h : i ≠ j) : upd f j v i = f i := by
  simp [upd, h]

theorem pend_j (j p0 p1 : Nat) (sq : Nat → Nat) : pend j p0 p1 sq j = p0 := by
  simp [pend, show ¬ (j + 1 ≤ j) by omega, show ¬ (j + 2 ≤ j) by omega]

theorem pend_j1 (j p0 p1 : Nat) (sq : Nat → Nat) : pend j p0 p1 sq (j + 1) = p1 + sq j := by
  simp [pend, show ¬ (j + 2 ≤ j + 1) by omega]

theorem pend_j2 (j p0 p1 : Nat) (sq : Nat → Nat) : pend j p0 p1 sq (j + 2) = sq (j + 1) + sq j := by
  simp [pend] <;> omega

theorem pend_ge (j p0 p1 : Nat) (sq : Nat → Nat) (i : Nat) (h : j + 3 ≤ i) :
    pend j p0 p1 sq i = sq (i - 1) + sq (i - 2) := by
  simp only [pend]
  rw [ite_eq_right (by omega), ite_eq_right (by omega), ite_eq_left (by omega), ite_eq_left (by omega)]
  omega

/-- moving the greedy one position forward -/
theorem pend_shift (j p0 p1 r : Nat) (sq : Nat → Nat) (i : Nat) (hi : j + 1 ≤ i) :
    pend j p0 p1 (upd sq j r) i = pend (j + 1) (p1 + r) r sq i := by
  rcases (show i = j + 1 ∨ i = j + 2 ∨ i = j + 3 ∨ j + 4 ≤ i by omega) with rfl | rfl | rfl | h
  · rw [pend_j1, pend_j, upd_same]
  · rw [pend_j2, show j + 2 = (j + 1) + 1 by omega, pend_j1, upd_same, upd_ne _ _ (by omega)]
    omega
  · rw [pend_ge _ _ _ _ _ (by omega), show j + 3 = (j + 1) + 2 by omega, pend_j2,
      upd_ne _ _ (by omega), upd_ne _ _ (by omega)]
    simp only [show j + 1 + 2 - 1 = j + 1 + 1 by omega, show j + 1 + 2 - 2 = j + 1 by omega]
  · rw [pend_ge _ _ _ _ _ (by omega), pend_ge _ _ _ _ _ (by omega),
      upd_ne _ _ (by omega), upd_ne _ _ (by omega)]

theorem grW_zero (w : Nat → Nat) (lim j p0 p1 : Nat) :
    grW w lim 0 j p0 p1 = (Nat.beq p0 0 && Nat.beq p1 0) := rfl

theorem grW_succ (w : Nat → Nat) (lim f j p0 p1 : Nat) :
    grW w lim (f + 1) j p0 p1 =
      cond (Nat.blt (w j) p0) false
        (cond (Nat.blt j lim)
          (grW w lim f (j + 1) (p1 + (w j - p0) % 3) ((w j - p0) % 3))
          (Nat.beq ((w j - p0) % 3) 0 && grW w lim f (j + 1) p1 0)) := rfl

theorem blt_false {a b : Nat} (h : ¬ a < b) : Nat.blt a b = false := by
  cases hb : Nat.blt a b
  · rfl
  · exact absurd (Nat.blt_eq.mp hb) h

/-- the invariant: the greedy from position `j` succeeds iff the suffix decomposes -/
theorem grW_iff (w : Nat → Nat) (lim n : Nat) (hl : lim = 0 ∨ lim + 2 ≤ n) :
    ∀ f j p0 p1, j + f = n → (grW w lim f j p0 p1 = true ↔ SufDec w lim n j p0 p1) := by
  intro f
  induction f with
  | zero =>
    intro j p0 p1 hj
    rw [grW_zero]
    simp only [Bool.and_eq_true, Nat.beq_eq]
    constructor
    · rintro ⟨rfl, rfl⟩
      exact ⟨fun _ => 0, fun _ => 0, by simp, by simp, by simp, fun i h1 h2 => by omega⟩
    · rintro ⟨tr, sq, -, h0, h1, -⟩
      exact ⟨Decidable.byContradiction fun h => by have := h0 h; omega,
             Decidable.byContradiction fun h => by have := h1 h; omega⟩
  | succ f ih =>
    intro j p0 p1 hj
    rw [grW_succ]
    by_cases hc : w j < p0
    · rw [Nat.blt_eq.mpr hc, Bool.cond_true]
      simp only [Bool.false_eq_true, false_iff]
      rintro ⟨tr, sq, -, -, -, he⟩
      have := he j (Nat.le_refl _) (by omega)
      rw [pend_j] at this
      omega
    rw [blt_false hc, Bool.cond_false]
    -- what the greedy does at position `j`, as an extension/restriction of witnesses
    have extend : ∀ r t0, w j - p0 = 3 * t0 + r → (r ≠ 0 → j < lim) →
        SufDec w lim n (j + 1) (p1 + r) r → SufDec w lim n j p0 p1 := by
      rintro r t0 hwr hrl ⟨tr, sq, hsq, h0, h1, he⟩
      refine ⟨upd tr j t0, upd sq j r, ?_, fun _ => by omega, fun hp => h0 (by omega), ?_⟩
      · intro i hi
        by_cases hij : i = j
        · subst hij; rw [upd_same] at hi; exact ⟨Nat.le_refl _, hrl hi⟩
        · rw [upd_ne _ _ hij] at hi
          have := hsq i hi; exact ⟨by omega, this.2⟩
      · intro i hi1 hi2
        by_cases hij : i = j
        · subst hij; rw [upd_same, upd_same, pend_j]; omega
        · rw [upd_ne _ _ hij, upd_ne _ _ hij, pend_shift _ _ _ _ _ _ (by omega)]
          exact he i (by omega) hi2
    have restrict : ∀ (tr sq : Nat → Nat), (∀ i, sq i ≠ 0 → j ≤ i ∧ i < lim) → (p1 ≠ 0 → j + 1 < n) →
        (∀ i, j ≤ i → i < n → w i = 3 * tr i + sq i + pend j p0 p1 sq i) →
        SufDec w lim n (j + 1) (p1 + sq j % 3) (sq j % 3) := by
      intro tr sq hsq h1 he
      have hfit : sq j ≠ 0 → j + 2 < n := fun h => by
        have := (hsq j h).2; rcases hl with hl | hl <;> omega
      refine ⟨fun i => tr i + (if j ≤ i ∧ i ≤ j + 2 then sq j / 3 else 0), upd sq j 0, ?_, ?_, ?_, ?_⟩
      · intro i hi
        by_cases hij : i = j
        · subst hij; simp at hi
        · rw [upd_ne _ _ hij] at hi
          have := hsq i hi; exact ⟨by omega, this.2⟩
      · intro hne
        by_cases hp : p1 = 0
        · exact Nat.lt_of_succ_lt (hfit (by omega))
        · exact h1 hp
      · intro hne; exact hfit (by omega)
      · intro i hi1 hi2
        have hw := he i (by omega) hi2
        dsimp only
        rcases (show i = j + 1 ∨ i = j + 2 ∨ i = j + 3 ∨ j + 4 ≤ i by omega) with rfl | rfl | rfl | h
        · rw [pend_j1] at hw
          rw [pend_j, upd_ne _ _ (by omega), ite_eq_left (by omega)]
          omega
        · rw [pend_j2] at hw
          rw [(pend_j1 (j + 1) _ _ _ : pend (j + 1) _ _ _ (j + 2) = _), upd_ne _ _ (by omega),
            upd_ne _ _ (by omega), ite_eq_left (by omega)]
          omega
        · rw [pend_ge _ _ _ _ _ (by omega)] at hw
          rw [(pend_j2 (j + 1) _ _ _ : pend (j + 1) _ _ _ (j + 3) = _), upd_ne _ _ (by omega),
            upd_ne _ _ (by omega), upd_ne _ _ (by omega), ite_eq_right (by omega)]
          simp only [show j + 3 - 1 = j + 2 by omega, show j + 3 - 2 = j + 1 by omega] at hw
          omega
        · rw [pend_ge _ _ _ _ _ (by omega)] at hw
          rw [pend_ge _ _ _ _ _ (by omega), upd_ne _ _ (by omega), upd_ne _ _ (by omega),
            upd_ne _ _ (by omega), ite_eq_right (by omega)]
          omega
    by_cases hlim : j < lim
    · rw [Nat.blt_eq.mpr hlim, Bool.cond_true, ih (j + 1) _ _ (by omega)]
      constructor
      · intro h
        exact extend _ ((w j - p0) / 3) (by omega) (fun _ => hlim) h
      · rintro ⟨tr, sq, hsq, -, h1, he⟩
        have hej := he j (Nat.le_refl _) (by omega)
        rw [pend_j] at hej
        have hr : (w j - p0) % 3 = sq j % 3 := by omega
        rw [hr]
        exact restrict tr sq hsq h1 he
    · rw [blt_false hlim, Bool.cond_false]
      simp only [Bool.and_eq_true, Nat.beq_eq]
      rw [ih (j + 1) _ _ (by omega)]
      constructor
      · rintro ⟨hmod, h⟩
        exact extend 0 ((w j - p0) / 3) (by omega) (by simp) (by simpa using h)
      · rintro ⟨tr, sq, hsq, -, h1, he⟩
        have hsj : sq j = 0 := Decidable.byContradiction fun h => by have := hsq j h; omega
        have hej := he j (Nat.le_refl _) (by omega)
        rw [pend_j] at hej
        refine ⟨by omega, ?_⟩
        have := restrict tr sq hsq h1 he
        rw [hsj] at this
        simpa using this

theorem localDec_iff_suf (w : Nat → Nat) (lim n : Nat) : LocalDec w lim n ↔ SufDec w lim n 0 0 0 := by
  constructor
  · rintro ⟨tr, sq, hsq, he⟩
    refine ⟨tr, sq, fun i hi => ⟨Nat.zero_le _, hsq i hi⟩, by simp, by simp, ?_⟩
    intro i _ hi
    rw [he i hi]
    simp [pend, seqCov] <;> omega
  · rintro ⟨tr, sq, hsq, -, -, he⟩
    refine ⟨tr, sq, fun i hi => (hsq i hi).2, ?_⟩
    intro i hi
    rw [he i (Nat.zero_le _) hi]
    simp [pend, seqCov] <;> omega

/-- **greedy correctness** -/
theorem grW_correct (w : Nat → Nat) (lim n : Nat) (hl : lim = 0 ∨ lim + 2 ≤ n) :
    grW w lim n 0 0 0 = true ↔ LocalDec w lim n := by
  rw [localDec_iff_suf, grW_iff w lim n hl n 0 0 0 (by omega)]

/-- the greedy only reads positions `j, j+1, …, j+f-1` -/
theorem grW_congr {w v : Nat → Nat} (lim : Nat) :
    ∀ f j p0 p1, (∀ i, j ≤ i → i < j + f → w i = v i) → grW w lim f j p0 p1 = grW v lim f j p0 p1 := by
  intro f
  induction f with
  | zero => intro j p0 p1 _; rfl
  | succ f ih =>
    intro j p0 p1 h
    rw [grW_succ, grW_succ, h j (Nat.le_refl _) (by omega),
      ih (j + 1) _ _ (fun i h1 h2 => h i (by omega) (by omega)),
      ih (j + 1) _ _ (fun i h1 h2 => h i (by omega) (by omega))]

end Tenpai
