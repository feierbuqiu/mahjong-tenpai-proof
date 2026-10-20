import Tenpai.Glue

/-! # Restricting a hand to some categories; the inert part as a list of melds -/

namespace Tenpai

/-- the part of `H` lying in the categories selected by the bit mask `cats` -/
def Fr (H : Counts) (cats : Nat) : Counts := fun s => if cats.testBit (s.val / 9) = true then H s else 0

theorem Fr_le (H : Counts) (cats : Nat) (s : Tile) : Fr H cats s ≤ H s := by
  unfold Fr; split <;> omega

theorem catF_Fr (H : Counts) (cats k j : Nat) (hk : k < 4) (hj : j < catLen k) :
    catF (extF (Fr H cats)) k j = if cats.testBit k = true then catF (extF H) k j else 0 := by
  have hlt := catLen_le k hk j hj
  have hd : (9 * k + j) / 9 = k := by unfold catLen at hj; split at hj <;> omega
  simp only [catF, extF, hlt, dite_true, Fr, hd]

theorem pkF_zero_fn (n : Nat) : pkF (fun _ => 0) n = 0 := by
  induction n with
  | zero => rfl
  | succ n ih => rw [pkF_succ, ih]; simp

theorem cvOf_Fr (H : Counts) (cats k : Nat) (hk : k < 4) :
    cvOf (Fr H cats) k = if cats.testBit k = true then cvOf H k else 0 := by
  unfold cvOf catPk
  rw [pkF_congr (g := fun j => if cats.testBit k = true then catF (extF H) k j else 0)
    (fun j hj => catF_Fr H cats k j hk hj)]
  split
  · next h => exact pkF_congr (fun j _ => by simp)
  · next h => rw [pkF_congr (g := fun _ => 0) (fun j _ => by simp), pkF_zero_fn]

theorem hsize_Fr (H : Counts) (cats k : Nat) (hk : k < 4) :
    hsize (Fr H cats) k = if cats.testBit k = true then hsize H k else 0 := by
  unfold hsize
  rw [sumF_congr (g := fun j => if cats.testBit k = true then catF (extF H) k j else 0)
    (fun j hj => catF_Fr H cats k j hk hj)]
  split
  · next h => exact sumF_congr (fun j _ => by simp)
  · next h =>
    rw [sumF_congr (g := fun _ => 0) (fun j _ => by simp)]
    clear h
    generalize catLen k = n
    induction n with
    | zero => rfl
    | succ n ih => rw [sumF_succ, ih]

theorem total_Fr (H : Counts) (cats : Nat) :
    total (Fr H cats) = (if cats.testBit 0 = true then hsize H 0 else 0) + (if cats.testBit 1 = true then hsize H 1 else 0) +
      (if cats.testBit 2 = true then hsize H 2 else 0) + (if cats.testBit 3 = true then hsize H 3 else 0) := by
  rw [total_eq_sizes, hsize_Fr H cats 0 (by omega), hsize_Fr H cats 1 (by omega), hsize_Fr H cats 2 (by omega),
    hsize_Fr H cats 3 (by omega)]

/-! ## meld decomposition of a part made of meld-complete categories -/

theorem meldDec_Fr (H : Counts) (hH : ∀ s, H s ≤ 4) (cats : Nat)
    (hM : ∀ k < 4, cats.testBit k = true → cM k (cvOf H k) = true) : MeldDec (Fr H cats) := by
  rw [meldDec_iff_isM _ (fun s => by have := Fr_le H cats s; have := hH s; omega)]
  intro k hk
  show cM k (cvOf (Fr H cats) k) = true
  rw [cvOf_Fr H cats k hk]
  split
  · next h => exact hM k hk h
  · exact cM_zero k hk

theorem mcount_ge (ms : List Meld) (m : Meld) (hm : m ∈ ms) (s : Tile) : m.count s ≤ mcount ms s := by
  induction ms with
  | nil => simp at hm
  | cons a ms ih =>
    simp only [mcount, List.map_cons, List.sum_cons] at ih ⊢
    rcases List.mem_cons.mp hm with rfl | hm
    · omega
    · have := ih hm; omega

theorem meld_count_tile (m : Meld) : 1 ≤ m.count m.tile := by
  cases m with
  | trip x => simp [Meld.count, Meld.tile]
  | seq x => simp [Meld.count, Meld.tile]

theorem pkF_sum_list (ms : List Meld) (g : Meld → Nat → Nat) (n : Nat) :
    pkF (fun t => (ms.map (fun m => g m t)).sum) n = (ms.map (fun m => pkF (g m) n)).sum := by
  induction ms with
  | nil => simp only [List.map_nil, List.sum_nil]; exact pkF_zero_fn n
  | cons m ms ih =>
    simp only [List.map_cons, List.sum_cons]
    rw [pkF_add, ih]

/-- the part selected by `cats` is a list of melds of those categories, packed as their sum -/
theorem Fr_melds (H : Counts) (hH : ∀ s, H s ≤ 4) (cats : Nat)
    (hM : ∀ k < 4, cats.testBit k = true → cM k (cvOf H k) = true) :
    ∃ ms : List Meld, (∀ m ∈ ms, m.Valid) ∧ (∀ m ∈ ms, meldPk m ∈ meldList cats) ∧
      (∀ s, Fr H cats s = mcount ms s) ∧ 3 * ms.length = total (Fr H cats) ∧
      pkF (extF (Fr H cats)) 34 = (ms.map meldPk).sum := by
  obtain ⟨ms, hv, he⟩ := meldDec_Fr H hH cats hM
  refine ⟨ms, hv, ?_, he, ?_, ?_⟩
  · intro m hm
    apply mem_meldList cats m (hv m hm)
    have h1 := meld_count_tile m
    have h2 := mcount_ge ms m hm m.tile
    have h3 := he m.tile
    unfold Fr at h3
    exact Decidable.byContradiction fun hb => by
      simp only [Bool.not_eq_true] at hb
      rw [hb] at h3
      simp at h3
      omega
  · rw [show Fr H cats = mcount ms from funext he, total_mcount ms hv]
  · have e : extF (Fr H cats) = fun t => (ms.map (fun m => extF m.count t)).sum := by
      funext t
      simp only [extF]
      split
      · next ht => rw [he]; rfl
      · next ht =>
        have : ∀ l : List Meld, 0 = (l.map (fun _ => (0 : Nat))).sum := by
          intro l
          induction l with
          | nil => rfl
          | cons a l ih => rw [List.map_cons, List.sum_cons, ← ih]
        exact this ms
    rw [e, pkF_sum_list]
    congr 1
    apply List.map_congr_left
    intro m hm
    exact (meldPk_eq m (hv m hm)).symm

/-! ## packed parts -/

theorem fld_shift36 (u x q : Nat) :
    fld (Nat.shiftLeft u (Nat.mul 36 x)) q = if 9 * x ≤ q then fld u (q - 9 * x) else 0 := by
  have hb : ∀ v, fld v q < 16 := fun v => by rw [fld_eq]; exact Nat.mod_lt _ (by omega)
  apply Nat.eq_of_testBit_eq
  intro r
  by_cases hr : r < 4
  · rw [← testBit_fld _ _ _ hr]
    show (u <<< (36 * x)).testBit (4 * q + r) = _
    rw [Nat.testBit_shiftLeft]
    split
    · next h9 =>
      rw [← testBit_fld _ _ _ hr]
      simp only [show 4 * q + r ≥ 36 * x by omega, decide_true, Bool.true_and]
      congr 1; omega
    · next h9 =>
      simp only [show ¬ (4 * q + r ≥ 36 * x) by omega, decide_false, Bool.false_and]
      simp
  · have h1 : ∀ v : Nat, v < 16 → v.testBit r = false := fun v hv =>
      Nat.testBit_lt_two_pow (Nat.lt_of_lt_of_le hv (by
        have : (16:Nat) = 2 ^ 4 := rfl
        rw [this]; exact Nat.pow_le_pow_right (by omega) (by omega)))
    rw [h1 _ (hb _)]
    split
    · rw [h1 _ (by rw [fld_eq]; exact Nat.mod_lt _ (by omega))]
    · simp

/-- the packed hand of a single category `x` -/
theorem pk_Fr_single (H : Counts) (hH : ∀ s, H s ≤ 4) (x : Nat) (hx : x < 4) :
    pkF (extF (Fr H (2 ^ x))) 34 = Nat.shiftLeft (cvOf H x) (Nat.mul 36 x) := by
  apply eq_of_fld_eq
  intro q
  rw [fld_shift36, fld_hand (Fr H (2 ^ x)) (fun s => by have := Fr_le H (2 ^ x) s; have := hH s; omega)]
  simp only [extF, Fr, Nat.testBit_two_pow]
  by_cases hq : q < 34
  · simp only [hq, dite_true]
    unfold cvOf catPk
    rw [fld_pkF _ _ (fun j _ => by have := catF_le4 H hH x j; omega)]
    by_cases hqx : q / 9 = x
    · subst hqx
      simp only [decide_true, ite_true, show 9 * (q / 9) ≤ q by omega]
      rw [ite_eq_left (show q - 9 * (q / 9) < catLen (q / 9) by unfold catLen; split <;> omega)]
      simp [catF, extF, show 9 * (q / 9) + (q - 9 * (q / 9)) = q by omega, hq]
    · have : decide (x = q / 9) = false := by simp; omega
      rw [this]
      simp only [Bool.false_eq_true, ite_false]
      split
      · rw [ite_eq_right]
        intro hlt
        exact hqx (cat_of_offset x q hx (by omega) hlt)
      · rfl
  · simp only [hq, dite_false]
    split
    · unfold cvOf catPk
      rw [fld_pkF _ _ (fun j _ => by have := catF_le4 H hH x j; omega)]
      rw [ite_eq_right]
      intro hlt
      have := catLen_le x hx _ hlt
      omega
    · rfl

/-- splitting a hand into two complementary parts -/
theorem pk_Fr_split (H : Counts) (a b : Nat) (h : ∀ k < 4, (a.testBit k = true ↔ ¬ b.testBit k = true)) :
    pkF (extF H) 34 = pkF (extF (Fr H a)) 34 + pkF (extF (Fr H b)) 34 := by
  rw [← pkF_add]
  apply pkF_congr
  intro t ht
  simp only [extF, ht, dite_true, Fr]
  have hk := h (t / 9) (by omega)
  by_cases ha : a.testBit (t / 9) = true
  · have hb : ¬ b.testBit (t / 9) = true := hk.mp ha
    simp [ha, hb]
  · have hb : b.testBit (t / 9) = true := Decidable.byContradiction fun hn => ha (hk.mpr hn)
    simp [ha, hb]

theorem Fr_union (H : Counts) (x y : Nat) (hxy : x ≠ y) :
    pkF (extF (Fr H (2 ^ x ||| 2 ^ y))) 34 = pkF (extF (Fr H (2 ^ x))) 34 + pkF (extF (Fr H (2 ^ y))) 34 := by
  rw [← pkF_add]
  apply pkF_congr
  intro t ht
  simp only [extF, ht, dite_true, Fr, Nat.testBit_or, Nat.testBit_two_pow]
  by_cases h1 : x = t / 9 <;> by_cases h2 : y = t / 9 <;> simp [h1, h2] <;> omega

end Tenpai
