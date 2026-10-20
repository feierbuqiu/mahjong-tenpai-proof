import Tenpai.Spec
import Tenpai.Greedy

/-!
# From meld lists (the specification) to the per-category greedy test

* a multiset is a sum of valid melds  ⟺  every category vector has a local count-form
  decomposition (`LocalDec`)  ⟺  the kernel test `isM` accepts each packed category vector.
-/

namespace Tenpai

/-! ## categories -/

/-- number of positions of category `k` (suits 9, honours 7) -/
def catLen (k : Nat) : Nat := if k < 3 then 9 else 7
/-- sequences may start at local positions `< catLim k` -/
def catLim (k : Nat) : Nat := if k < 3 then 7 else 0

/-- extension of a count function to all of `Nat` -/
def extF (F : Counts) : Nat → Nat := fun t => if h : t < 34 then F ⟨t, h⟩ else 0

/-- local view of category `k` of a vector -/
def catF (v : Nat → Nat) (k : Nat) : Nat → Nat := fun j => v (9 * k + j)

/-- packed local vector of category `k` -/
def catPk (v : Nat → Nat) (k : Nat) : Nat := pkF (catF v k) (catLen k)

theorem catLim_ok (k : Nat) : catLim k = 0 ∨ catLim k + 2 ≤ catLen k := by
  unfold catLim catLen; split <;> omega

/-- tile `t < 34` lies in category `k` -/
theorem inCat_iff (k t : Nat) (hk : k < 4) (ht : t < 34) :
    (9 * k ≤ t ∧ t < 9 * k + catLen k) ↔ t / 9 = k := by
  unfold catLen; split <;> omega

/-! ## meld lists -/

def Meld.tripAt (t : Nat) : Meld → Nat
  | .trip x => if x.val = t then 1 else 0
  | .seq _ => 0

def Meld.seqAt (t : Nat) : Meld → Nat
  | .seq x => if x.val = t then 1 else 0
  | .trip _ => 0

def trC (ms : List Meld) (t : Nat) : Nat := (ms.map (Meld.tripAt t)).sum
def sqC (ms : List Meld) (t : Nat) : Nat := (ms.map (Meld.seqAt t)).sum
def mcount (ms : List Meld) (s : Tile) : Nat := (ms.map (fun m => m.count s)).sum

theorem trC_append (a b : List Meld) (t : Nat) : trC (a ++ b) t = trC a t + trC b t := by
  simp [trC]
theorem sqC_append (a b : List Meld) (t : Nat) : sqC (a ++ b) t = sqC a t + sqC b t := by
  simp [sqC]
theorem mcount_append (a b : List Meld) (s : Tile) : mcount (a ++ b) s = mcount a s + mcount b s := by
  simp [mcount]

theorem sum_replicate_map (k : Nat) (m : Meld) (f : Meld → Nat) :
    ((List.replicate k m).map f).sum = k * f m := by
  induction k with
  | zero => simp
  | succ k ih => rw [List.replicate_succ, List.map_cons, List.sum_cons, ih, Nat.succ_mul]; omega

theorem seqCov_add (f g : Nat → Nat) (s : Nat) :
    seqCov (fun t => f t + g t) s = seqCov f s + seqCov g s := by
  simp only [seqCov]; split <;> split <;> omega

theorem meld_count_eq (m : Meld) (hv : m.Valid) (s : Tile) :
    m.count s = 3 * m.tripAt s.val + m.seqAt s.val + seqCov (fun t => m.seqAt t) s.val := by
  have hs := s.isLt
  cases m with
  | trip x =>
    simp only [Meld.count, Meld.tripAt, Meld.seqAt, seqCov, Fin.ext_iff]
    repeat' split
    all_goals omega
  | seq x =>
    have hv' : x.val < 27 ∧ x.val % 9 ≤ 6 := hv
    simp only [Meld.count, Meld.tripAt, Meld.seqAt, seqCov]
    repeat' split
    all_goals omega

theorem mcount_eq (ms : List Meld) (hv : ∀ m ∈ ms, m.Valid) (s : Tile) :
    mcount ms s = 3 * trC ms s.val + sqC ms s.val + seqCov (sqC ms) s.val := by
  induction ms with
  | nil => simp [mcount, trC, sqC, seqCov]
  | cons m ms ih =>
    have e : sqC (m :: ms) = fun t => m.seqAt t + sqC ms t := by
      funext t; simp [sqC]
    have ih' := ih (fun m' h => hv m' (List.mem_cons_of_mem _ h))
    simp only [mcount, List.map_cons, List.sum_cons] at ih' ⊢
    rw [ih', e, seqCov_add, meld_count_eq m (hv m List.mem_cons_self)]
    simp only [trC, sqC, List.map_cons, List.sum_cons]
    omega

theorem sqC_support (ms : List Meld) (hv : ∀ m ∈ ms, m.Valid) (t : Nat) (h : sqC ms t ≠ 0) :
    t < 27 ∧ t % 9 ≤ 6 := by
  induction ms with
  | nil => simp [sqC] at h
  | cons m ms ih =>
    simp only [sqC, List.map_cons, List.sum_cons] at h
    by_cases h' : m.seqAt t = 0
    · exact ih (fun m' hm => hv m' (List.mem_cons_of_mem _ hm)) (by simp only [sqC]; omega)
    · cases m with
      | trip x => simp [Meld.seqAt] at h'
      | seq x =>
        have := hv (.seq x) List.mem_cons_self
        simp only [Meld.Valid] at this
        simp only [Meld.seqAt] at h'
        split at h'
        · omega
        · simp at h'

/-! ## building a meld list for one category from a count form -/

/-- melds of category `k`: `tr j` triplets and `sq j` sequences at tile `9k + j`, `j < n` -/
def mkCat (k : Nat) (tr sq : Nat → Nat) : Nat → List Meld
  | 0 => []
  | n + 1 => mkCat k tr sq n ++
      (if h : 9 * k + n < 34 then
        List.replicate (tr n) (.trip ⟨9 * k + n, h⟩) ++ List.replicate (sq n) (.seq ⟨9 * k + n, h⟩)
       else [])

theorem trC_rep_trip (c : Nat) (x : Tile) (t : Nat) :
    trC (List.replicate c (.trip x)) t = if x.val = t then c else 0 := by
  simp only [trC, sum_replicate_map, Meld.tripAt]; split <;> simp
theorem trC_rep_seq (c : Nat) (x : Tile) (t : Nat) : trC (List.replicate c (.seq x)) t = 0 := by
  simp only [trC, sum_replicate_map, Meld.tripAt]; simp
theorem sqC_rep_trip (c : Nat) (x : Tile) (t : Nat) : sqC (List.replicate c (.trip x)) t = 0 := by
  simp only [sqC, sum_replicate_map, Meld.seqAt]; simp
theorem sqC_rep_seq (c : Nat) (x : Tile) (t : Nat) :
    sqC (List.replicate c (.seq x)) t = if x.val = t then c else 0 := by
  simp only [sqC, sum_replicate_map, Meld.seqAt]; split <;> simp

theorem trC_mkCat (k : Nat) (tr sq : Nat → Nat) (t : Nat) :
    ∀ n, trC (mkCat k tr sq n) t = if 9 * k ≤ t ∧ t < 9 * k + n ∧ t < 34 then tr (t - 9 * k) else 0
  | 0 => by rw [ite_eq_right (by omega)]; rfl
  | n + 1 => by
    rw [mkCat, trC_append, trC_mkCat k tr sq t n]
    by_cases hn : 9 * k + n < 34
    · simp only [hn, ↓reduceDIte]
      rw [trC_append, trC_rep_trip, trC_rep_seq]
      by_cases ht : t = 9 * k + n
      · subst ht
        rw [ite_eq_right (by omega), ite_eq_left rfl, ite_eq_left (by omega)]
        simp
      · rw [ite_eq_right (show ¬ (9 * k + n = t) by omega)]
        by_cases hc : 9 * k ≤ t ∧ t < 9 * k + n ∧ t < 34
        · rw [ite_eq_left hc, ite_eq_left (by omega)]; simp
        · rw [ite_eq_right hc, ite_eq_right (by omega)]
    · simp only [hn, ↓reduceDIte]
      simp only [trC, List.map_nil, List.sum_nil, Nat.add_zero]
      by_cases hc : 9 * k ≤ t ∧ t < 9 * k + n ∧ t < 34
      · rw [ite_eq_left hc, ite_eq_left (by omega)]
      · rw [ite_eq_right hc, ite_eq_right (by omega)]

theorem sqC_mkCat (k : Nat) (tr sq : Nat → Nat) (t : Nat) :
    ∀ n, sqC (mkCat k tr sq n) t = if 9 * k ≤ t ∧ t < 9 * k + n ∧ t < 34 then sq (t - 9 * k) else 0
  | 0 => by rw [ite_eq_right (by omega)]; rfl
  | n + 1 => by
    rw [mkCat, sqC_append, sqC_mkCat k tr sq t n]
    by_cases hn : 9 * k + n < 34
    · simp only [hn, ↓reduceDIte]
      rw [sqC_append, sqC_rep_trip, sqC_rep_seq]
      by_cases ht : t = 9 * k + n
      · subst ht
        rw [ite_eq_right (by omega), ite_eq_left rfl, ite_eq_left (by omega)]
        simp
      · rw [ite_eq_right (show ¬ (9 * k + n = t) by omega)]
        by_cases hc : 9 * k ≤ t ∧ t < 9 * k + n ∧ t < 34
        · rw [ite_eq_left hc, ite_eq_left (by omega)]; simp
        · rw [ite_eq_right hc, ite_eq_right (by omega)]
    · simp only [hn, ↓reduceDIte]
      simp only [sqC, List.map_nil, List.sum_nil, Nat.add_zero]
      by_cases hc : 9 * k ≤ t ∧ t < 9 * k + n ∧ t < 34
      · rw [ite_eq_left hc, ite_eq_left (by omega)]
      · rw [ite_eq_right hc, ite_eq_right (by omega)]

theorem mkCat_valid (k : Nat) (tr sq : Nat → Nat) (hsq : ∀ j, sq j ≠ 0 → j < catLim k) :
    ∀ n, ∀ m ∈ mkCat k tr sq n, m.Valid
  | 0 => by simp [mkCat]
  | n + 1 => by
    intro m hm
    simp only [mkCat, List.mem_append] at hm
    rcases hm with hm | hm
    · exact mkCat_valid k tr sq hsq n m hm
    · split at hm
      · next hn =>
        simp only [List.mem_append, List.mem_replicate] at hm
        rcases hm with ⟨-, rfl⟩ | ⟨hk, rfl⟩
        · trivial
        · have := hsq n (by omega)
          unfold catLim at this
          show 9 * k + n < 27 ∧ (9 * k + n) % 9 ≤ 6
          split at this <;> omega
      · simp at hm

/-- a local decomposition of category `k` gives melds whose sum is exactly the category part -/
theorem cat_melds (F : Counts) (k : Nat) (hk : k < 4)
    (h : LocalDec (catF (extF F) k) (catLim k) (catLen k)) :
    ∃ ms : List Meld, (∀ m ∈ ms, m.Valid) ∧ ∀ s : Tile, mcount ms s = if s.val / 9 = k then F s else 0 := by
  obtain ⟨tr, sq, hsq, he⟩ := h
  have hv := mkCat_valid k tr sq hsq (catLen k)
  refine ⟨mkCat k tr sq (catLen k), hv, ?_⟩
  intro s
  have hs := s.isLt
  have hlen : ∀ j, sq j ≠ 0 → j + 2 < catLen k := fun j h => by
    have := hsq j h; unfold catLim at this; unfold catLen; split at this <;> split <;> omega
  let SQ : Nat → Nat := fun t => if 9 * k ≤ t ∧ t < 9 * k + catLen k ∧ t < 34 then sq (t - 9 * k) else 0
  have hSQ : sqC (mkCat k tr sq (catLen k)) = SQ := by funext t; rw [sqC_mkCat]
  have hz : ∀ t, SQ t ≠ 0 → 9 * k ≤ t ∧ t + 2 < 9 * k + catLen k := by
    intro t h
    simp only [SQ] at h
    split at h
    · next hr => have := hlen _ h; omega
    · simp at h
  rw [mcount_eq _ hv, trC_mkCat, hSQ]
  by_cases hin : s.val / 9 = k
  · rw [ite_eq_left hin]
    have hr := (inCat_iff k s.val hk hs).mpr hin
    have hj : s.val - 9 * k < catLen k := by omega
    have := he (s.val - 9 * k) hj
    simp only [catF, extF, show 9 * k + (s.val - 9 * k) = s.val by omega, hs, dite_true] at this
    rw [this, ite_eq_left (show 9 * k ≤ s.val ∧ s.val < 9 * k + catLen k ∧ s.val < 34 by omega)]
    have e0 : SQ s.val = sq (s.val - 9 * k) := by
      simp only [SQ]; rw [ite_eq_left (by omega)]
    rw [e0]
    congr 1
    simp only [seqCov]
    have c1 : (if 1 ≤ s.val then SQ (s.val - 1) else 0) =
        (if 1 ≤ s.val - 9 * k then sq (s.val - 9 * k - 1) else 0) := by
      by_cases h1 : 1 ≤ s.val - 9 * k
      · rw [ite_eq_left h1, ite_eq_left (by omega)]
        simp only [SQ]; rw [ite_eq_left (by omega)]; congr 1; omega
      · rw [ite_eq_right h1]
        split
        · exact Decidable.byContradiction fun h => by have := hz _ h; omega
        · rfl
    have c2 : (if 2 ≤ s.val then SQ (s.val - 2) else 0) =
        (if 2 ≤ s.val - 9 * k then sq (s.val - 9 * k - 2) else 0) := by
      by_cases h2 : 2 ≤ s.val - 9 * k
      · rw [ite_eq_left h2, ite_eq_left (by omega)]
        simp only [SQ]; rw [ite_eq_left (by omega)]; congr 1; omega
      · rw [ite_eq_right h2]
        split
        · exact Decidable.byContradiction fun h => by have := hz _ h; omega
        · rfl
    rw [c1, c2]
  · rw [ite_eq_right hin]
    have hr : ¬ (9 * k ≤ s.val ∧ s.val < 9 * k + catLen k) := fun h => hin ((inCat_iff k s.val hk hs).mp h)
    rw [ite_eq_right (show ¬ (9 * k ≤ s.val ∧ s.val < 9 * k + catLen k ∧ s.val < 34) by omega)]
    have e0 : SQ s.val = 0 := by
      simp only [SQ]; rw [ite_eq_right (by omega)]
    rw [e0]
    simp only [seqCov]
    have c1 : (if 1 ≤ s.val then SQ (s.val - 1) else 0) = 0 := by
      split
      · exact Decidable.byContradiction fun h => by have := hz _ h; omega
      · rfl
    have c2 : (if 2 ≤ s.val then SQ (s.val - 2) else 0) = 0 := by
      split
      · exact Decidable.byContradiction fun h => by have := hz _ h; omega
      · rfl
    rw [c1, c2]

/-! ## meld decompositions -/

/-- `F` is a sum of valid melds -/
def MeldDec (F : Counts) : Prop :=
  ∃ ms : List Meld, (∀ m ∈ ms, m.Valid) ∧ ∀ s, F s = mcount ms s

theorem meldDec_iff_cats (F : Counts) :
    MeldDec F ↔ ∀ k < 4, LocalDec (catF (extF F) k) (catLim k) (catLen k) := by
  constructor
  · rintro ⟨ms, hv, hF⟩ k hk
    refine ⟨fun j => if j < catLen k then trC ms (9 * k + j) else 0,
            fun j => if j < catLen k then sqC ms (9 * k + j) else 0, ?_, ?_⟩
    · intro j hj
      dsimp only at hj
      split at hj
      · next hjl =>
        have := sqC_support ms hv _ hj
        unfold catLim; unfold catLen at hjl; split <;> split at hjl <;> omega
      · simp at hj
    · intro j hj
      have hlt : 9 * k + j < 34 := by unfold catLen at hj; split at hj <;> omega
      simp only [catF, extF, hlt, dite_true]
      rw [hF, mcount_eq ms hv, ite_eq_left hj, ite_eq_left hj]
      congr 1
      have z : ∀ t, t % 9 ≥ 7 → sqC ms t = 0 := fun t ht =>
        Decidable.byContradiction fun h => by have := sqC_support ms hv t h; omega
      simp only [seqCov]
      have c1 : (if 1 ≤ 9 * k + j then sqC ms (9 * k + j - 1) else 0) =
          (if 1 ≤ j then (if j - 1 < catLen k then sqC ms (9 * k + (j - 1)) else 0) else 0) := by
        by_cases h1 : 1 ≤ j
        · rw [ite_eq_left (by omega), ite_eq_left h1, ite_eq_left (by omega)]
          congr 1; omega
        · rw [ite_eq_right h1]
          split
          · exact z _ (by omega)
          · rfl
      have c2 : (if 2 ≤ 9 * k + j then sqC ms (9 * k + j - 2) else 0) =
          (if 2 ≤ j then (if j - 2 < catLen k then sqC ms (9 * k + (j - 2)) else 0) else 0) := by
        by_cases h2 : 2 ≤ j
        · rw [ite_eq_left (by omega), ite_eq_left h2, ite_eq_left (by omega)]
          congr 1; omega
        · rw [ite_eq_right h2]
          split
          · exact z _ (by omega)
          · rfl
      rw [c1, c2]
  · intro h
    obtain ⟨m0, v0, e0⟩ := cat_melds F 0 (by omega) (h 0 (by omega))
    obtain ⟨m1, v1, e1⟩ := cat_melds F 1 (by omega) (h 1 (by omega))
    obtain ⟨m2, v2, e2⟩ := cat_melds F 2 (by omega) (h 2 (by omega))
    obtain ⟨m3, v3, e3⟩ := cat_melds F 3 (by omega) (h 3 (by omega))
    refine ⟨m0 ++ m1 ++ m2 ++ m3, ?_, ?_⟩
    · intro m hm
      simp only [List.mem_append] at hm
      rcases hm with ((hm | hm) | hm) | hm
      · exact v0 m hm
      · exact v1 m hm
      · exact v2 m hm
      · exact v3 m hm
    · intro s
      simp only [mcount_append, e0, e1, e2, e3]
      have := s.isLt
      rcases (show s.val / 9 = 0 ∨ s.val / 9 = 1 ∨ s.val / 9 = 2 ∨ s.val / 9 = 3 by omega)
        with h | h | h | h <;> simp [h]

/-! ## the packed test -/

theorem isM_iff (v : Nat → Nat) (k : Nat) (hv : ∀ j < catLen k, catF v k j < 16) :
    isM (catLen k) (catLim k) (catPk v k) = true ↔ LocalDec (catF v k) (catLim k) (catLen k) := by
  unfold isM catPk
  rw [grW_congr (v := catF v k) (catLim k) (catLen k) 0 0 0 (fun i _ hi => by
    rw [fld_pkF _ _ hv, ite_eq_left (by omega)])]
  exact grW_correct _ _ _ (catLim_ok k)

/-- **a multiset splits into melds iff every packed category vector passes `isM`** -/
theorem meldDec_iff_isM (F : Counts) (hF : ∀ s, F s < 16) :
    MeldDec F ↔ ∀ k < 4, isM (catLen k) (catLim k) (catPk (extF F) k) = true := by
  rw [meldDec_iff_cats]
  apply forall_congr'; intro k
  apply imp_congr_right; intro hk
  rw [isM_iff]
  intro j _
  simp only [catF, extF]
  split
  · exact hF _
  · omega

end Tenpai
