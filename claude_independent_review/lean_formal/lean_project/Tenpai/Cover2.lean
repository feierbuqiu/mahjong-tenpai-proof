import Tenpai.Cover

/-! # Coverage for hands with a standard wait -/

namespace Tenpai

theorem hsize_le13 (H : Counts) (hH : IsHand H) (k : Nat) (hk : k < 4) : hsize H k ≤ 13 := by
  have := total_eq_sizes H; have := hH.1
  rcases (show k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 by omega) with rfl | rfl | rfl | rfl <;> omega

theorem sum_sizes (H : Counts) (hH : IsHand H) : hsize H 0 + hsize H 1 + hsize H 2 + hsize H 3 = 13 := by
  rw [← total_eq_sizes]; exact hH.1

theorem wStd_congr (cv cv' : Nat → Nat) (h : ∀ k < 4, cv k = cv' k) : wStd cv = wStd cv' := by
  rw [wStd_eq, wStd_eq]
  unfold wStdP
  refine lor_congr (orBelow_congr fun x hx => ?_) (orBelow_congr fun x hx => orBelow_congr fun y hy => ?_)
  · rw [allBelow_congr (g := fun k => Nat.beq k x || cM k (cv' k)) (fun k hk => by rw [h k hk]), h x hx]
  · rw [allBelow_congr (g := fun k => Nat.beq k x || Nat.beq k y || cM k (cv' k)) (fun k hk => by rw [h k hk]),
      h x hx, h y hy]

theorem allL_four (f : Nat → Bool) (h : ∀ k < 4, f k = true) : allL f [0, 1, 2, 3] = true := by
  show (f 0 && (f 1 && (f 2 && (f 3 && true)))) = true
  rw [h 0 (by omega), h 1 (by omega), h 2 (by omega), h 3 (by omega)]; rfl

theorem singles_le (H : Counts) (hH : ∀ s, H s ≤ 4) (z : Tile) (hz : Shaped7 H z) (k : Nat) (hk : k < 4) :
    singles (catLen k) (cvOf H k) ≤ 1 := by
  have h := singles_sum H hH
  rw [shaped7_singles H z hz] at h
  simp only [Nat.add_eq] at h
  rcases (show k = 0 ∨ k = 1 ∨ k = 2 ∨ k = 3 by omega) with rfl | rfl | rfl | rfl
  · show singles 9 (cvOf H 0) ≤ 1; omega
  · show singles 9 (cvOf H 1) ≤ 1; omega
  · show singles 9 (cvOf H 2) ≤ 1; omega
  · show singles 7 (cvOf H 3) ≤ 1; omega

/-! ## T4: seven-pairs shaped hands with a standard wait -/

theorem shaped7_le2 (H : Counts) (z : Tile) (hz : Shaped7 H z) : ∀ s, H s ≤ 2 := by
  intro s; by_cases h : s = z
  · subst h; have := hz.1; omega
  · rcases hz.2.1 s h with h' | h' <;> omega

/-- the category vectors of a seven-pairs shaped hand are in the T4 candidate lists -/
theorem t4mem (H : Counts) (hH : IsHand H) (z : Tile) (hz : Shaped7 H z) (act : Nat → Bool)
    (hinert : ∀ k < 4, act k = false → cM k (cvOf H k) = true) (k : Nat) (hk : k < 4) :
    cvOf H k ∈ t4list (act k) k (hsize H k) := by
  have hc : cvOf H k ∈ cand k (hsize H k) := by
    unfold cand
    rw [List.mem_filter]
    exact ⟨cv_mem_vecsD H 2 (shaped7_le2 H z hz) k, Nat.ble_eq.mpr (singles_le H hH.2 z hz k hk)⟩
  unfold t4list
  rw [force_eq]
  cases ha : act k
  · rw [Bool.cond_false, List.mem_filter]; exact ⟨hc, hinert k hk ha⟩
  · rw [Bool.cond_true]; exact hc

theorem singTotal_eq (H : Counts) (hH : IsHand H) (z : Tile) (hz : Shaped7 H z) :
    singTotal (sel4 (cvOf H 0) (cvOf H 1) (cvOf H 2) (cvOf H 3)) = 1 := by
  have hsel := sel4_cv (cvOf H)
  unfold singTotal
  simp only [force_eq]
  rw [hsel 0 (by omega), hsel 1 (by omega), hsel 2 (by omega), hsel 3 (by omega)]
  exact (singles_sum H hH.2).trans (shaped7_singles H z hz)

theorem singBits_sel (cv : Nat → Nat) : singBits (sel4 (cv 0) (cv 1) (cv 2) (cv 3)) = singBits cv := by
  unfold singBits
  exact orBelow_congr (fun k hk => by rw [sel4_cv cv k hk])

theorem singBits_eq (H : Counts) (hH : IsHand H) (z : Tile) (hz : Shaped7 H z) :
    singBits (cvOf H) = 2 ^ z.val := by
  have key : ∀ i, (singBits (cvOf H)).testBit i = true ↔ i < 34 ∧ ∃ h : i < 34, H ⟨i, h⟩ = 1 := by
    intro i
    unfold singBits
    rw [testBit_orBelow]
    constructor
    · rintro ⟨k, hk, hb⟩
      rw [force_eq, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_maskBelow, Bool.and_eq_true,
        decide_eq_true_eq, Nat.beq_eq] at hb
      obtain ⟨h9, hj, h1⟩ := hb
      have hi := catLen_le k hk _ hj
      have hik : i / 9 = k := cat_of_offset k i hk h9 hj
      refine ⟨by omega, by omega, ?_⟩
      have : fld (cvOf H (i / 9)) (i % 9) = H ⟨i, by omega⟩ := fld_catPk H hH.2 ⟨i, by omega⟩
      rw [hik, show i % 9 = i - 9 * k by omega] at this
      rw [← this]; exact h1
    · rintro ⟨hi, h', h1⟩
      refine ⟨i / 9, by omega, ?_⟩
      rw [force_eq, testBit_shift9, Bool.and_eq_true, decide_eq_true_eq, testBit_maskBelow, Bool.and_eq_true,
        decide_eq_true_eq, Nat.beq_eq]
      have : fld (cvOf H (i / 9)) (i % 9) = H ⟨i, hi⟩ := fld_catPk H hH.2 ⟨i, hi⟩
      refine ⟨by omega, by unfold catLen; split <;> omega, ?_⟩
      rw [show i - 9 * (i / 9) = i % 9 by omega, this]; exact h1
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_two_pow]
  cases hb : (singBits (cvOf H)).testBit i
  · symm
    simp only [decide_eq_false_iff_not]
    intro e; subst e
    have := (key z.val).mpr ⟨z.isLt, z.isLt, by simpa using hz.1⟩
    rw [hb] at this; exact Bool.noConfusion this
  · obtain ⟨hi, _, h1⟩ := (key i).mp hb
    have : (⟨i, hi⟩ : Tile) = z := Decidable.byContradiction fun hne => by
      have := hz.2.1 ⟨i, hi⟩ hne; omega
    subst this; simp

theorem cover_T4A (tree : PTree (List Nat)) (x : Nat) (h4 : t4okA tree x = true) (H : Counts) (hH : IsHand H)
    (hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t))) (hA : PatA H x) (z : Tile) (hz : Shaped7 H z)
    (hn4 : 4 ≤ hsize H x) : Covered tree H := by
  have hA' := hA
  obtain ⟨hx, hM, hW⟩ := hA
  have hs := sum_sizes H hH
  have hsel := sel4_cv (cvOf H)
  have hshape : shape1 x (sel4 (hsize H 0) (hsize H 1) (hsize H 2) (hsize H 3)) = true := by
    have hn := sel4_cv (hsize H)
    unfold shape1
    rw [hn x hx]
    simp only [Bool.and_eq_true, Nat.beq_eq, Nat.ble_eq]
    refine ⟨⟨wp_mod H hH x hW, hn4⟩, allL_four _ (fun k hk => ?_)⟩
    rw [hn k hk]
    by_cases hkx : k = x
    · subst hkx; simp
    · have := cM_mod H hH k (hM k hk hkx)
      have hb : Nat.beq k x = false := by
        cases h : Nat.beq k x
        · rfl
        · exact absurd (Nat.eq_of_beq_eq_true h) hkx
      rw [hb, Bool.false_or, Nat.beq_eq]; exact this
  have hmem := t4mem H hH z hz (fun k => Nat.beq k x) (fun k hk ha => hM k hk (by
    intro e; subst e; simp at ha))
  have ht := t4A_sound tree x h4 (hsize H 0) (hsize H 1) (hsize H 2) (hsize H 3)
    (by have := hsize_le13 H hH 0 (by omega); omega) (by have := hsize_le13 H hH 1 (by omega); omega)
    (by have := hsize_le13 H hH 2 (by omega); omega) hs hshape _ _ _ _
    (hmem 0 (by omega)) (hmem 1 (by omega)) (hmem 2 (by omega)) (hmem 3 (by omega))
  unfold t4handA at ht
  rw [singTotal_eq H hH z hz, force_eq, hsel x hx, singBits_sel, singBits_eq H hH z hz] at ht
  have hb : Nat.beq (cWP x (cvOf H x)) 0 = false := by
    cases h : Nat.beq (cWP x (cvOf H x)) 0
    · rfl
    · exact absurd (Nat.eq_of_beq_eq_true h) hW
  have hg : glue (sel4 (cvOf H 0) (cvOf H 1) (cvOf H 2) (cvOf H 3)) = glue (cvOf H) := by
    unfold glue; rw [hsel 0 (by omega), hsel 1 (by omega), hsel 2 (by omega), hsel 3 (by omega)]
  rw [hb, hg, glue_cvOf, Nat.beq_refl] at ht
  simp only [Bool.not_true, Bool.false_or] at ht
  have hw : wAll (cvOf H) = Nat.lor (Nat.shiftLeft (cWP x (cvOf H x)) (Nat.mul 9 x)) (2 ^ z.val) := by
    apply wAll_eq_of H hH
    · intro i hi
      rw [testBit_lor', shift9_high _ x hx (fun j hj => cWP_high x _ j hj) i hi, two_pow_high z.val z.isLt i hi]
      rfl
    · intro t
      rw [W_noK H hH hnoK, testBit_lor', Bool.or_eq_true, stdW_patA H hH x hA', Nat.testBit_two_pow]
      constructor
      · rintro (h | h)
        · exact Or.inl h
        · right; have := shaped7_unique H z t hz h; subst this; simp
      · rintro (h | h)
        · exact Or.inl h
        · right; simp only [decide_eq_true_eq] at h
          have : z = t := Fin.ext h
          subst this; exact hz
  have := hasCode_sound tree _ _ ht
  unfold Covered; rw [hw]; exact this

end Tenpai
