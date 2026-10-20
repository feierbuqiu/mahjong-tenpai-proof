import Tenpai.Cover2

/-! # Coverage for one or two active categories, and the coverage theorem -/

namespace Tenpai

/-! ## pattern (a): one active category -/

theorem cover_A (tree : PTree (List Nat)) (cuts : Nat → List Nat) (hc : Checked tree cuts)
    (H : Counts) (hH : IsHand H) (hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t)))
    (x : Nat) (hA : PatA H x) (ts : Nat) (_hts : StdW H ts) : Covered tree H := by
  obtain ⟨hx, hM, hW⟩ := hA
  have hn1 : hsize H x % 3 = 1 := wp_mod H hH x hW
  have hn13 := hsize_le13 H hH x hx
  have hsum := sum_sizes H hH
  have hle := hH.2
  -- the inert part: all categories except `x`
  have hcatsx : ∀ k < 4, (catsExcept x).testBit k = true → cM k (cvOf H k) = true := by
    intro k hk hb
    exact hM k hk ((testBit_catsExcept x k hx).mp hb).2
  obtain ⟨ms, hmv, hmL, hmF, hmlen, hmpk⟩ := Fr_melds H hle (catsExcept x) hcatsx
  have htotF : total (Fr H (catsExcept x)) = 13 - hsize H x := by
    rw [total_Fr]
    have b : ∀ k < 4, (catsExcept x).testBit k = !(decide (k = x)) := by
      intro k hk
      cases h : (catsExcept x).testBit k
      · have hn : ¬ (k < 4 ∧ k ≠ x) := fun hh => by
          rw [(testBit_catsExcept x k hx).mpr hh] at h; exact Bool.noConfusion h
        have : k = x := by omega
        simp [this]
      · have := (testBit_catsExcept x k hx).mp h; simp [this.2]
    rw [b 0 (by omega), b 1 (by omega), b 2 (by omega), b 3 (by omega)]
    rcases (show x = 0 ∨ x = 1 ∨ x = 2 ∨ x = 3 by omega) with rfl | rfl | rfl | rfl <;> simp <;> omega
  have hsplit : pkF (extF H) 34 = Nat.shiftLeft (cvOf H x) (Nat.mul 36 x) + (ms.map meldPk).sum := by
    rw [pk_Fr_split H (2 ^ x) (catsExcept x), pk_Fr_single H hle x hx, hmpk]
    intro k hk
    rw [Nat.testBit_two_pow, testBit_catsExcept x k hx]
    constructor
    · intro h; simp at h; omega
    · intro h; simp; omega
  by_cases hn : hsize H x = 1
  · ---------------- single wait (tanki)
    obtain ⟨j, hj, hj1, hj0⟩ := sumF_one (catF (extF H) x) (catLen x) hn
    have hcv : cvOf H x = 16 ^ j := by
      unfold cvOf catPk
      rw [← pkF_single j _ hj]
      exact pkF_congr (fun i hi => by by_cases h : i = j <;> simp_all)
    let z : Tile := ⟨9 * x + j, catLen_le x hx j hj⟩
    have hzx : z.val / 9 = x := by show (9 * x + j) / 9 = x; unfold catLen at hj; split at hj <;> omega
    have hHz : H z = 1 := by
      have : catF (extF H) x j = H z := by simp [catF, extF, z, catLen_le x hx j hj]
      omega
    have hw : wAll (cvOf H) = 2 ^ z.val := by
      apply wAll_eq_of H hH _ (two_pow_high z.val z.isLt)
      intro t
      rw [W_noK H hH hnoK, stdW_patA H hH x ⟨hx, hM, hW⟩, hcv, cWP_single_tile x hx j hj, Nat.testBit_two_pow,
        testBit_shift9, Nat.testBit_two_pow]
      constructor
      · rintro (h | h7)
        · simp only [Bool.and_eq_true, decide_eq_true_eq] at h
          simp only [decide_eq_true_eq]; show 9 * x + j = t.val; omega
        · have : t = z := Decidable.byContradiction fun hne => by
            have := h7.2.1 z (fun e => hne e.symm); omega
          subst this; simp
      · intro h
        simp only [decide_eq_true_eq] at h
        left
        simp only [Bool.and_eq_true, decide_eq_true_eq]
        show 9 * x ≤ t.val ∧ j = t.val - 9 * x
        have : z.val = 9 * x + j := rfl
        omega
    -- a meld of the inert part
    have hms : ms ≠ [] := by
      intro e; rw [e] at hmlen; simp at hmlen; omega
    obtain ⟨m, hm⟩ := List.exists_mem_of_ne_nil ms hms
    have h0 := t0_sound tree hc.t0 z.val z.isLt (meldPk m) (by rw [hzx]; exact hmL m hm)
    let G : Counts := fun s => (if s = z then 1 else 0) + m.count s
    have hmz : m.count z = 0 := by
      have h1 := mcount_ge ms m hm z
      have h2 := hmF z
      unfold Fr at h2
      rw [hzx] at h2
      have : (catsExcept x).testBit x = false := by
        cases h : (catsExcept x).testBit x
        · rfl
        · have := (testBit_catsExcept x x hx).mp h; omega
      rw [this] at h2
      simp at h2
      omega
    have hGH : ∀ s, G s ≤ H s := by
      intro s
      simp only [G]
      by_cases hs : s = z
      · subst hs; rw [hmz]; simp [hHz]
      · have h1 := mcount_ge ms m hm s
        have h2 := hmF s
        have h3 := Fr_le H (catsExcept x) s
        simp [hs]; omega
    have hpk : pkF (extF G) 34 = 16 ^ z.val + meldPk m := by
      simp only [G]
      rw [pk_add_counts, pk_indicator, meldPk_eq m (hmv m hm)]
      omega
    have := hasCode_mono tree hc.valid _ _ _ h0
      (by rw [← hpk]; exact small_hand G (fun s => Nat.le_trans (hGH s) (hle s)))
      (small_hand H hle) (by rw [← hpk]; exact sub_fld G H hGH hle)
    unfold Covered; rw [hw]; exact this
  · by_cases h7 : ∃ z, Shaped7 H z
    · ---------------- seven-pairs shaped: check T4
      obtain ⟨z, hz⟩ := h7
      exact cover_T4A tree x (hc.t4A x hx) H hH hnoK ⟨hx, hM, hW⟩ z hz (by omega)
    · ---------------- check T1
      have hno7 : ∀ t : Tile, ¬ Shaped7 H t := fun t h => h7 ⟨t, h⟩
      have hw : wAll (cvOf H) = Nat.shiftLeft (cWP x (cvOf H x)) (Nat.mul 9 x) := by
        apply wAll_eq_of H hH _ (shift9_high _ x hx (fun j hj => cWP_high x _ j hj))
        intro t
        rw [W_noK H hH hnoK, ← stdW_patA H hH x ⟨hx, hM, hW⟩]
        constructor
        · rintro (h | h); exact h; exact absurd h (hno7 t)
        · exact Or.inl
      have hnset : hsize H x = 4 ∨ hsize H x = 7 ∨ hsize H x = 10 ∨ hsize H x = 13 := by omega
      have h1 := t1_sound tree x (hsize H x) (cvOf H x) (hc.t1 x hx _ hnset _ (cv_mem_vecs H hle x))
      rcases h1 with h1 | h1 | ⟨h4, h1⟩
      · exfalso
        obtain ⟨j, hj⟩ := testBit_of_ne_zero hW
        have : (Nat.shiftLeft (cWP x (cvOf H x)) (Nat.mul 9 x)).testBit (9 * x + j) = true := by
          rw [testBit_shift9]; simp [hj]
        rw [h1] at this; simp at this
      · have hA := pk_Fr_single H hle x hx
        have := hasCode_mono tree hc.valid _ _ _ h1
          (by rw [← hA]; exact small_hand _ (fun s => Nat.le_trans (Fr_le H _ s) (hle s)))
          (small_hand H hle) (by rw [← hA]; exact sub_fld _ H (Fr_le H _) hle)
        unfold Covered; rw [hw]; exact this
      · -- exception: the nine inert tiles are three melds
        have hlen3 : ms.length = 3 := by rw [htotF, h4] at hmlen; omega
        obtain ⟨m1, m2, m3, rfl⟩ : ∃ m1 m2 m3, ms = [m1, m2, m3] := by
          match ms, hlen3 with
          | [m1, m2, m3], _ => exact ⟨m1, m2, m3, rfl⟩
        · simp only [List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, Nat.add_zero] at hsplit
          let A := Nat.shiftLeft (cvOf H x) (Nat.mul 36 x)
          have hAF := pk_Fr_single H hle x hx
          have hpart : ∀ (mm : Meld), mm = m1 ∨ mm = m2 ∨ mm = m3 →
              Small (A + meldPk mm) ∧ ∀ t < 34, fld (A + meldPk mm) t ≤ fld (A + meldPk m1 + meldPk m2 + meldPk m3) t := by
            intro mm hmm
            have hmem : mm ∈ [m1, m2, m3] := by rcases hmm with rfl | rfl | rfl <;> simp
            let G : Counts := fun s => Fr H (2 ^ x) s + mm.count s
            have hGH : ∀ s, G s ≤ H s := by
              intro s
              have h1 := mcount_ge [m1, m2, m3] mm hmem s
              have h2 := hmF s
              have h3 : Fr H (2 ^ x) s + Fr H (catsExcept x) s = H s := by
                unfold Fr
                have := testBit_catsExcept x (s.val / 9) hx
                rw [Nat.testBit_two_pow]
                have hs9 : s.val / 9 < 4 := by have := s.isLt; omega
                by_cases hxs : x = s.val / 9
                · have : (catsExcept x).testBit (s.val / 9) = false := by
                    cases h : (catsExcept x).testBit (s.val / 9)
                    · rfl
                    · have := (testBit_catsExcept x _ hx).mp h; omega
                  rw [this]; simp [hxs]
                · have : (catsExcept x).testBit (s.val / 9) = true :=
                    (testBit_catsExcept x _ hx).mpr ⟨hs9, fun e => hxs e.symm⟩
                  rw [this]; simp [hxs]
              simp only [G]; omega
            have hpk : pkF (extF G) 34 = A + meldPk mm := by
              simp only [G]; rw [pk_add_counts, hAF, meldPk_eq mm (hmv mm hmem)]
            have e : A + meldPk m1 + meldPk m2 + meldPk m3 = pkF (extF H) 34 := by
              rw [hsplit]; simp only [A]; omega
            rw [← hpk, e]
            exact ⟨small_hand G (fun s => Nat.le_trans (hGH s) (hle s)), sub_fld G H hGH hle⟩
          have e : A + meldPk m1 + meldPk m2 + meldPk m3 = pkF (extF H) 34 := by
            rw [hsplit]; simp only [A]; omega
          have := meldRule_sound tree hc.valid _ A (catsExcept x) h1 (meldPk m1) (meldPk m2) (meldPk m3)
            (hmL m1 (by simp)) (hmL m2 (by simp)) (hmL m3 (by simp))
            (by rw [e]; exact small_hand H hle)
            (fun i hi => by
              rcases hi with rfl | rfl | rfl
              · exact hpart m1 (Or.inl rfl)
              · exact hpart m2 (Or.inr (Or.inl rfl))
              · exact hpart m3 (Or.inr (Or.inr rfl)))
          rw [e] at this
          unfold Covered; rw [hw]; exact this

end Tenpai
