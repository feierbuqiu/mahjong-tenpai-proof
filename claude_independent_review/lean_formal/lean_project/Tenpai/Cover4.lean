import Tenpai.Cover3

/-! # Coverage for two active categories; the coverage theorem -/

namespace Tenpai

theorem lor_comm' (a b : Nat) : Nat.lor a b = Nat.lor b a := by
  apply Nat.eq_of_testBit_eq; intro i
  rw [testBit_lor', testBit_lor', Bool.or_comm]

/-- inert total for two active categories `a < b` -/
theorem total_Fr2 (H : Counts) (hH : IsHand H) (a b : Nat) (hab : a < b) (hb4 : b < 4) :
    total (Fr H (catsExcept2 a b)) = 13 - (hsize H a + hsize H b) := by
  rw [total_Fr]
  have hs := sum_sizes H hH
  rcases (show a = 0 ∨ a = 1 ∨ a = 2 by omega) with rfl | rfl | rfl <;>
  rcases (show b = 1 ∨ b = 2 ∨ b = 3 by omega) with rfl | rfl | rfl <;>
    first | omega | (simp [catsExcept2, catsExcept]; omega) | skip
  all_goals (simp (config := {decide := true}) <;> omega)

/-- the class mask of pattern (b) for an ordered pair of categories `a < b` -/
noncomputable def maskB (H : Counts) (a b : Nat) : Nat :=
  Nat.lor (cond (cP b (cvOf H b)) (Nat.shiftLeft (cWM a (cvOf H a)) (Nat.mul 9 a)) 0)
          (cond (cP a (cvOf H a)) (Nat.shiftLeft (cWM b (cvOf H b)) (Nat.mul 9 b)) 0)

theorem maskB_comm (H : Counts) (a b : Nat) : maskB H a b = maskB H b a := lor_comm' _ _

theorem maskB_high (H : Counts) (a b : Nat) (ha : a < 4) (hb : b < 4) (i : Nat) (hi : 34 ≤ i) :
    (maskB H a b).testBit i = false := by
  unfold maskB
  rw [testBit_lor', Bool.or_eq_false_iff]
  constructor
  · cases cP b (cvOf H b)
    · simp
    · exact shift9_high _ a ha (fun j hj => cWM_high a _ j hj) i hi
  · cases cP a (cvOf H a)
    · simp
    · exact shift9_high _ b hb (fun j hj => cWM_high b _ j hj) i hi

theorem maskB2_sel (x y : Nat) (hx : x < 4) (hy : y < 4) (H : Counts) :
    maskB2 x y (sel4 (cvOf H 0) (cvOf H 1) (cvOf H 2) (cvOf H 3)) = maskB H x y := by
  have hsel := sel4_cv (cvOf H)
  unfold maskB2 maskB
  simp only [force_eq]
  rw [hsel x hx, hsel y hy]

/-- T4 for two active categories `x < y` -/
theorem cover_T4B (tree : PTree (List Nat)) (x y : Nat) (hxy : x < y) (hy4 : y < 4)
    (h4 : t4okB tree x y = true) (H : Counts) (hH : IsHand H)
    (hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t)))
    (hM : ∀ k < 4, k ≠ x → k ≠ y → cM k (cvOf H k) = true)
    (hnx : hsize H x % 3 = 2) (hny : hsize H y % 3 = 2)
    (hstd : ∀ t, StdW H t ↔ (maskB H x y).testBit t = true) (hnz : maskB H x y ≠ 0)
    (z : Tile) (hz : Shaped7 H z) : Covered tree H := by
  have hx4 : x < 4 := by omega
  have hs := sum_sizes H hH
  have hsel := sel4_cv (cvOf H)
  have hshape : shape2 x y (sel4 (hsize H 0) (hsize H 1) (hsize H 2) (hsize H 3)) = true := by
    have hn := sel4_cv (hsize H)
    unfold shape2
    rw [hn x hx4, hn y hy4]
    simp only [Bool.and_eq_true, Nat.beq_eq]
    refine ⟨⟨hnx, hny⟩, allL_four _ (fun k hk => ?_)⟩
    rw [hn k hk]
    by_cases hkx : k = x
    · subst hkx; simp
    · by_cases hky : k = y
      · subst hky; simp
      · have := cM_mod H hH k (hM k hk hkx hky)
        have b1 : Nat.beq k x = false := by
          cases h : Nat.beq k x
          · rfl
          · exact absurd (Nat.eq_of_beq_eq_true h) hkx
        have b2 : Nat.beq k y = false := by
          cases h : Nat.beq k y
          · rfl
          · exact absurd (Nat.eq_of_beq_eq_true h) hky
        rw [b1, b2, Bool.false_or, Bool.false_or, Nat.beq_eq]; exact this
  have hmem := t4mem H hH z hz (fun k => Nat.beq k x || Nat.beq k y) (fun k hk ha => by
    simp only [Bool.or_eq_false_iff] at ha
    apply hM k hk
    · intro e; subst e; simp at ha
    · intro e; subst e; simp at ha)
  have ht := t4B_sound tree x y h4 (hsize H 0) (hsize H 1) (hsize H 2) (hsize H 3)
    (by have := hsize_le13 H hH 0 (by omega); omega) (by have := hsize_le13 H hH 1 (by omega); omega)
    (by have := hsize_le13 H hH 2 (by omega); omega) hs hshape _ _ _ _
    (hmem 0 (by omega)) (hmem 1 (by omega)) (hmem 2 (by omega)) (hmem 3 (by omega))
  unfold t4handB at ht
  rw [singTotal_eq H hH z hz, maskB2_sel x y hx4 hy4, singBits_sel, singBits_eq H hH z hz] at ht
  have hb : Nat.beq (maskB H x y) 0 = false := by
    cases h : Nat.beq (maskB H x y) 0
    · rfl
    · exact absurd (Nat.eq_of_beq_eq_true h) hnz
  have hg : glue (sel4 (cvOf H 0) (cvOf H 1) (cvOf H 2) (cvOf H 3)) = glue (cvOf H) := by
    unfold glue; rw [hsel 0 (by omega), hsel 1 (by omega), hsel 2 (by omega), hsel 3 (by omega)]
  rw [hb, hg, glue_cvOf, Nat.beq_refl] at ht
  simp only [Bool.not_true, Bool.false_or] at ht
  have hw : wAll (cvOf H) = Nat.lor (maskB H x y) (2 ^ z.val) := by
    apply wAll_eq_of H hH
    · intro i hi
      rw [testBit_lor', maskB_high H x y hx4 hy4 i hi, two_pow_high z.val z.isLt i hi]
      rfl
    · intro t
      rw [W_noK H hH hnoK, testBit_lor', Bool.or_eq_true, hstd, Nat.testBit_two_pow]
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

/-- pattern (b) with the two active categories ordered `a < b` (not seven-pairs shaped) -/
theorem cover_B_core (tree : PTree (List Nat)) (cuts : Nat → List Nat) (hc : Checked tree cuts)
    (H : Counts) (hH : IsHand H) (a b : Nat) (hab : a < b) (hb4 : b < 4)
    (hw : wAll (cvOf H) = maskB H a b) (hnz : maskB H a b ≠ 0)
    (hM : ∀ k < 4, k ≠ a → k ≠ b → cM k (cvOf H k) = true)
    (hna : hsize H a = 2 ∨ hsize H a = 5 ∨ hsize H a = 8 ∨ hsize H a = 11)
    (hnb : hsize H b = 2 ∨ hsize H b = 5 ∨ hsize H b = 8 ∨ hsize H b = 11)
    (hab13 : hsize H a + hsize H b ≤ 13) : Covered tree H := by
  have hle := hH.2
  have ha4 : a < 4 := by omega
  have habne : a ≠ b := by omega
  have h2 := hc.t2 a b hab hb4 _ _ hna hnb hab13 (cvOf H a) (cv_mem_vecs H hle a) (cvOf H b) (cv_mem_vecs H hle b)
  unfold T2unit at h2
  simp only at h2
  have hmask : Nat.lor (cond (cP b (cvOf H b)) (Nat.shiftLeft (cWM a (cvOf H a)) (Nat.mul 9 a)) 0)
      (cond (cP a (cvOf H a)) (Nat.shiftLeft (cWM b (cvOf H b)) (Nat.mul 9 b)) 0) = maskB H a b := rfl
  rw [hmask] at h2
  have hAct : Nat.add (Nat.shiftLeft (cvOf H a) (Nat.mul 36 a)) (Nat.shiftLeft (cvOf H b) (Nat.mul 36 b))
      = pkF (extF (Fr H (2 ^ a ||| 2 ^ b))) 34 := by
    rw [Fr_union H a b habne, pk_Fr_single H hle a ha4, pk_Fr_single H hle b hb4]; rfl
  rcases h2 with h2 | h2 | ⟨h4, h2⟩
  · exact absurd h2 hnz
  · rw [hAct] at h2
    have := hasCode_mono tree hc.valid _ _ _ h2
      (small_hand _ (fun s => Nat.le_trans (Fr_le H _ s) (hle s)))
      (small_hand H hle) (sub_fld _ H (Fr_le H _) hle)
    unfold Covered; rw [hw]; exact this
  · -- exception: nine inert tiles, three melds
    have hcats : ∀ k < 4, (catsExcept2 a b).testBit k = true → cM k (cvOf H k) = true := by
      intro k hk hbit
      have := (testBit_catsExcept2 a b k ha4 hb4 habne).mp hbit
      exact hM k hk this.2.1 this.2.2
    obtain ⟨ms, hmv, hmL, hmF, hmlen, hmpk⟩ := Fr_melds H hle (catsExcept2 a b) hcats
    have hbits : ∀ k < 4, ((2 ^ a ||| 2 ^ b).testBit k = true ↔ ¬ (catsExcept2 a b).testBit k = true) := by
      intro k hk
      rw [Nat.testBit_or, Nat.testBit_two_pow, Nat.testBit_two_pow, testBit_catsExcept2 a b k ha4 hb4 habne]
      simp only [Bool.or_eq_true, decide_eq_true_eq]
      omega
    have htotF : total (Fr H (catsExcept2 a b)) = 9 := by
      rw [total_Fr2 H hH a b hab hb4]; omega
    have hlen3 : ms.length = 3 := by rw [htotF] at hmlen; omega
    obtain ⟨m1, m2, m3, rfl⟩ : ∃ m1 m2 m3, ms = [m1, m2, m3] := by
      match ms, hlen3 with
      | [m1, m2, m3], _ => exact ⟨m1, m2, m3, rfl⟩
    simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, Nat.add_zero] at hmpk
    let A := Nat.add (Nat.shiftLeft (cvOf H a) (Nat.mul 36 a)) (Nat.shiftLeft (cvOf H b) (Nat.mul 36 b))
    have hsplit : pkF (extF H) 34 = A + (meldPk m1 + (meldPk m2 + meldPk m3)) := by
      rw [pk_Fr_split H _ _ hbits, hmpk, ← hAct]
    have e : A + meldPk m1 + meldPk m2 + meldPk m3 = pkF (extF H) 34 := by rw [hsplit]; omega
    have hpart : ∀ (mm : Meld), mm = m1 ∨ mm = m2 ∨ mm = m3 →
        Small (A + meldPk mm) ∧ ∀ t < 34, fld (A + meldPk mm) t ≤ fld (A + meldPk m1 + meldPk m2 + meldPk m3) t := by
      intro mm hmm
      have hmem : mm ∈ [m1, m2, m3] := by rcases hmm with rfl | rfl | rfl <;> simp
      let G : Counts := fun s => Fr H (2 ^ a ||| 2 ^ b) s + mm.count s
      have hGH : ∀ s, G s ≤ H s := by
        intro s
        have h1 := mcount_ge [m1, m2, m3] mm hmem s
        have h2 := hmF s
        have h3 : Fr H (2 ^ a ||| 2 ^ b) s + Fr H (catsExcept2 a b) s = H s := by
          unfold Fr
          have hs9 : s.val / 9 < 4 := by have := s.isLt; omega
          have hb := hbits (s.val / 9) hs9
          cases h : (2 ^ a ||| 2 ^ b).testBit (s.val / 9)
          · have : (catsExcept2 a b).testBit (s.val / 9) = true :=
              Decidable.byContradiction fun hn => by rw [h] at hb; exact absurd (hb.mpr hn) (by simp)
            simp [this]
          · have : (catsExcept2 a b).testBit (s.val / 9) = false := by
              cases h' : (catsExcept2 a b).testBit (s.val / 9)
              · rfl
              · exact absurd h' (hb.mp h)
            simp [this]
        simp only [G]; omega
      have hpk : pkF (extF G) 34 = A + meldPk mm := by
        simp only [G]; rw [pk_add_counts, ← hAct, meldPk_eq mm (hmv mm hmem)]
      rw [← hpk, e]
      exact ⟨small_hand G (fun s => Nat.le_trans (hGH s) (hle s)), sub_fld G H hGH hle⟩
    have := meldRule_sound tree hc.valid _ A (catsExcept2 a b) h2 (meldPk m1) (meldPk m2) (meldPk m3)
      (hmL m1 (by simp)) (hmL m2 (by simp)) (hmL m3 (by simp))
      (by rw [e]; exact small_hand H hle)
      (fun i hi => by
        rcases hi with rfl | rfl | rfl
        · exact hpart m1 (Or.inl rfl)
        · exact hpart m2 (Or.inr (Or.inl rfl))
        · exact hpart m3 (Or.inr (Or.inr rfl)))
    rw [e] at this
    unfold Covered; rw [hw]; exact this

/-- pattern (b): two active categories `x ≠ y`, the pair in `y` -/
theorem cover_B (tree : PTree (List Nat)) (cuts : Nat → List Nat) (hc : Checked tree cuts)
    (H : Counts) (hH : IsHand H) (hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t)))
    (x y : Nat) (hB : PatB H x y) (ts : Nat) (_hts : StdW H ts) : Covered tree H := by
  have hB' := hB
  obtain ⟨hx, hy, hxy, hPy, hM, hW⟩ := hB
  have hnx : hsize H x % 3 = 2 := wm_mod H hH x hW
  have hny : hsize H y % 3 = 2 := cP_mod H hH y hPy
  have hsum := sum_sizes H hH
  have hx13 := hsize_le13 H hH x hx
  have hy13 := hsize_le13 H hH y hy
  have hxy13 : hsize H x + hsize H y ≤ 13 := by
    rcases (show x = 0 ∨ x = 1 ∨ x = 2 ∨ x = 3 by omega) with rfl | rfl | rfl | rfl <;>
    rcases (show y = 0 ∨ y = 1 ∨ y = 2 ∨ y = 3 by omega) with rfl | rfl | rfl | rfl <;> omega
  by_cases h7 : ∃ z, Shaped7 H z
  · ---------------- seven-pairs shaped: check T4 (orient the pair)
    obtain ⟨z, hz⟩ := h7
    have hstd : ∀ t, StdW H t ↔ (maskB H x y).testBit t = true := fun t => by
      unfold maskB; exact stdW_patB H hH x y hB' t
    have hnz : maskB H x y ≠ 0 := by
      obtain ⟨j, hj⟩ := testBit_of_ne_zero hW
      apply ne_zero_of_testBit (j := 9 * x + j)
      unfold maskB
      rw [testBit_lor', hPy, Bool.cond_true, testBit_shift9]
      simp [hj]
    rcases Nat.lt_or_gt_of_ne hxy with hlt | hgt
    · exact cover_T4B tree x y hlt hy (hc.t4B x y hlt hy) H hH hnoK (fun k hk h1 h2 => hM k hk h1 h2)
        hnx hny hstd hnz z hz
    · rw [maskB_comm] at hnz
      exact cover_T4B tree y x hgt hx (hc.t4B y x hgt hx) H hH hnoK (fun k hk h1 h2 => hM k hk h2 h1)
        hny hnx (fun t => by rw [maskB_comm]; exact hstd t) hnz z hz
  · ---------------- check T2 (orient the pair)
    have hno7 : ∀ t : Tile, ¬ Shaped7 H t := fun t h => h7 ⟨t, h⟩
    have hw : wAll (cvOf H) = maskB H x y := by
      apply wAll_eq_of H hH _ (maskB_high H x y hx hy)
      intro t
      unfold maskB
      rw [W_noK H hH hnoK, ← stdW_patB H hH x y hB']
      constructor
      · rintro (h | h); exact h; exact absurd h (hno7 t)
      · exact Or.inl
    have hnz : maskB H x y ≠ 0 := by
      obtain ⟨j, hj⟩ := testBit_of_ne_zero hW
      apply ne_zero_of_testBit (j := 9 * x + j)
      unfold maskB
      rw [testBit_lor', hPy, Bool.cond_true, testBit_shift9]
      simp [hj]
    have hsz : ∀ k, (k = x ∨ k = y) → (hsize H k = 2 ∨ hsize H k = 5 ∨ hsize H k = 8 ∨ hsize H k = 11) := by
      intro k hk; rcases hk with rfl | rfl <;> omega
    rcases Nat.lt_or_gt_of_ne hxy with hlt | hgt
    · exact cover_B_core tree cuts hc H hH x y hlt hy hw hnz (fun k hk h1 h2 => hM k hk h1 h2)
        (hsz x (Or.inl rfl)) (hsz y (Or.inr rfl)) hxy13
    · rw [maskB_comm] at hw hnz
      exact cover_B_core tree cuts hc H hH y x hgt hx hw hnz (fun k hk h1 h2 => hM k hk h2 h1)
        (hsz y (Or.inr rfl)) (hsz x (Or.inl rfl)) (by omega)


/-- **coverage**: if all checks passed, every input hand contains a code of its own class -/
theorem cover (tree : PTree (List Nat)) (cuts : Nat → List Nat) (hc : Checked tree cuts)
    (H : Counts) (hH : InH H) : Covered tree H := by
  obtain ⟨hHand, t0, hw0⟩ := hH
  by_cases hK : ∃ t : Tile, H t < 4 ∧ IsKokushi (addTile H t)
  · obtain ⟨t, ht4, hk⟩ := hK
    exact cover_K tree hc.k H t ht4 hk
  · have hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t)) := fun t h => hK ⟨t, h⟩
    by_cases hS : ∃ t : Tile, StdW H t.val
    · obtain ⟨ts, hts⟩ := hS
      rcases pattern_of_stdW H hHand ts.val hts with ⟨x, hA⟩ | ⟨x, y, hB⟩
      · exact cover_A tree cuts hc H hHand hnoK x hA ts.val hts
      · exact cover_B tree cuts hc H hHand hnoK x y hB ts.val hts
    · have hnoS : ∀ t : Tile, ¬ StdW H t.val := fun t h => hS ⟨t, h⟩
      rcases (W_noK H hHand hnoK t0).mp hw0 with h | h
      · exact absurd h (hnoS t0)
      · exact cover_7 tree cuts hc.valid hc.t3 H hHand hnoK hnoS t0 h

end Tenpai
