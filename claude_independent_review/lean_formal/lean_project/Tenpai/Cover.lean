import Tenpai.Cover0

/-!
# Coverage: every input hand contains a code of its own class

Assuming the finite checks passed, every `H ∈ ℋ` contains (as a sub-multiset) some code of the
class `W(H)` in the plan.  Case analysis:
* a thirteen-orphans wait → one of 169 hands (check K);
* no standard wait → seven pairs only (check T3, pigeonhole over five groups);
* a standard wait → one active category (T0 single wait / T1 / T4) or two (T2 / T4).
-/

namespace Tenpai

/-- all finite checks passed for the plan `tree` -/
structure Checked (tree : PTree (List Nat)) (cuts : Nat → List Nat) : Prop where
  valid : TreeValid tree
  t0 : t0ok tree = true
  t1 : ∀ k < 4, ∀ n, (n = 4 ∨ n = 7 ∨ n = 10 ∨ n = 13) → ∀ u ∈ vecs (catLen k) n, t1unit tree k n u = true
  t2 : ∀ x y, x < y → y < 4 → ∀ nx ny, (nx = 2 ∨ nx = 5 ∨ nx = 8 ∨ nx = 11) →
    (ny = 2 ∨ ny = 5 ∨ ny = 8 ∨ ny = 11) → nx + ny ≤ 13 →
    ∀ u ∈ vecs (catLen x) nx, ∀ v ∈ vecs (catLen y) ny, T2unit tree x y nx ny u v
  t3 : t3ok tree cuts = true
  t4A : ∀ x < 4, t4okA tree x = true
  t4B : ∀ x y, x < y → y < 4 → t4okB tree x y = true
  k : kOK tree = true

/-- the goal for a hand -/
def Covered (tree : PTree (List Nat)) (H : Counts) : Prop :=
  ∃ e ∈ classCodes tree (wAll (cvOf H)), fits (codeVec e) (pkF (extF H) 34) = true

/-! ## the wait set without thirteen-orphans waits -/

theorem W_noK (H : Counts) (hH : IsHand H) (hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t)))
    (t : Tile) : W H t ↔ StdW H t.val ∨ Shaped7 H t := by
  rw [stdW_iff_standard H hH, ← sevenW_iff]
  unfold W IsWinning
  constructor
  · rintro ⟨h4, -, hs | h7 | hk⟩
    · exact Or.inl ⟨h4, hs⟩
    · exact Or.inr ⟨h4, h7⟩
    · exact absurd ⟨h4, hk⟩ (hnoK t)
  · rintro (⟨h4, hs⟩ | ⟨h4, h7⟩)
    · exact ⟨h4, addTile_le H hH.2 t h4, Or.inl hs⟩
    · exact ⟨h4, addTile_le H hH.2 t h4, Or.inr (Or.inl h7)⟩

theorem wAll_eq_of (H : Counts) (hH : IsHand H) (M : Nat) (hM : ∀ i, 34 ≤ i → M.testBit i = false)
    (h : ∀ t : Tile, W H t ↔ M.testBit t.val = true) : wAll (cvOf H) = M := by
  apply mask_eq_of (wAll_high H hH) hM
  intro i hi
  rw [wAll_correct H hH ⟨i, hi⟩, h ⟨i, hi⟩]

theorem two_pow_high (z : Nat) (hz : z < 34) : ∀ i, 34 ≤ i → (2 ^ z).testBit i = false := by
  intro i hi; rw [Nat.testBit_two_pow]; simp; omega

/-! ## packed pieces of hands -/

theorem pk_indicator (z : Tile) (c : Nat) :
    pkF (extF (fun s => if s = z then c else 0)) 34 = c * 16 ^ z.val := by
  rw [← pkF_single z.val 34 z.isLt, ← pkF_mul_const]
  apply pkF_congr
  intro j hj
  simp only [extF, hj, dite_true, Fin.ext_iff]
  split <;> simp_all

theorem pk_add_counts (F G : Counts) :
    pkF (extF (fun s => F s + G s)) 34 = pkF (extF F) 34 + pkF (extF G) 34 := by
  rw [← pkF_add]
  apply pkF_congr
  intro j hj
  simp [extF, hj]

/-! ## thirteen orphans -/

theorem cover_K (tree : PTree (List Nat)) (hk : kOK tree = true) (H : Counts) (t : Tile)
    (_ht4 : H t < 4) (hkok : IsKokushi (addTile H t)) : Covered tree H := by
  have hto := kok_orphan H t hkok
  obtain ⟨o, ho, he⟩ := hkok
  have hext : extF H = kokF o.val t.val := by
    funext s
    unfold extF kokF
    by_cases hs : s < 34
    · simp only [hs, dite_true, ite_true]
      have h1 := he ⟨s, hs⟩
      simp only [addTile] at h1
      have hor : (isOrphB s = true) ↔ IsOrphan ⟨s, hs⟩ := isOrphB_iff ⟨s, hs⟩
      have ht' : ((⟨s, hs⟩ : Tile) = t) ↔ s = t.val := by
        constructor
        · intro e; rw [← e]
        · intro e; exact Fin.ext e
      have ho' : ((⟨s, hs⟩ : Tile) = o) ↔ s = o.val := by
        constructor
        · intro e; rw [← e]
        · intro e; exact Fin.ext e
      by_cases a1 : s = t.val <;> by_cases a2 : s = o.val <;> by_cases a3 : IsOrphan (⟨s, hs⟩ : Tile) <;>
        simp_all
    · simp only [hs, dite_false, ite_false]
  have hcv : cvOf H = kokCv o.val t.val := by
    funext k; unfold cvOf catPk kokCv; rw [hext]
  have hc := k_sound tree hk o.val t.val o.isLt t.isLt ((isOrphB_iff o).mpr ho) ((isOrphB_iff t).mpr hto)
  rw [← hcv, glue_cvOf] at hc
  exact hasCode_sound tree _ _ hc

/-! ## seven pairs only -/

theorem cover_7 (tree : PTree (List Nat)) (cuts : Nat → List Nat) (hv : TreeValid tree)
    (h3 : t3ok tree cuts = true) (H : Counts) (hH : IsHand H)
    (hnoK : ∀ t : Tile, ¬ (H t < 4 ∧ IsKokushi (addTile H t))) (hnoS : ∀ t : Tile, ¬ StdW H t.val)
    (z : Tile) (hz : Shaped7 H z) : Covered tree H := by
  have hw : wAll (cvOf H) = 2 ^ z.val := by
    apply wAll_eq_of H hH _ (two_pow_high z.val z.isLt)
    intro t
    rw [W_noK H hH hnoK, Nat.testBit_two_pow]
    constructor
    · rintro (hs | h7)
      · exact absurd hs (hnoS t)
      · have := shaped7_unique H z t hz h7; subst this; simp
    · intro h
      simp only [decide_eq_true_eq] at h
      have : z = t := Fin.ext h
      subst this; exact Or.inr hz
  -- the six pair tiles and the pigeonhole over five groups
  let P := (List.finRange 34).filter (fun s => H s = 2)
  have hPn : P.Nodup := nodup_filter _ _ (List.nodup_finRange 34)
  have hPl : P.length = 6 := by rw [← List.countP_eq_length_filter]; exact hz.2.2
  have hg := t3_sound tree cuts h3 z.val z.isLt
  obtain ⟨a, ha, b, hb, hab, hgab⟩ := pigeonhole (fun s : Tile => grpOf (cuts z.val) s.val) 5 P hPn
    (by omega) (fun s _ => by have := hg.1 s.val; omega)
  have haP : H a = 2 := by have := (List.mem_filter.mp ha).2; simpa using this
  have hbP : H b = 2 := by have := (List.mem_filter.mp hb).2; simpa using this
  have haz : a ≠ z := fun e => by subst e; have := hz.1; omega
  have hbz : b ≠ z := fun e => by subst e; have := hz.1; omega
  -- order the two tiles
  have key : ∀ x y : Tile, H x = 2 → H y = 2 → x ≠ z → y ≠ z → x.val < y.val →
      grpOf (cuts z.val) x.val = grpOf (cuts z.val) y.val → Covered tree H := by
    intro x y hx hy hxz hyz hxy hgxy
    have hc := hg.2 x.val y.val x.isLt y.isLt hxy (fun e => hxz (Fin.ext e)) (fun e => hyz (Fin.ext e)) hgxy
    let G : Counts := fun s => (if s = z then 1 else 0) + ((if s = x then 2 else 0) + (if s = y then 2 else 0))
    have hGH : ∀ s, G s ≤ H s := by
      intro s
      simp only [G]
      by_cases s1 : s = z
      · subst s1; simp [hxz.symm, hyz.symm, hz.1]
      · by_cases s2 : s = x
        · subst s2; have : s ≠ y := fun e => by subst e; omega
          simp [s1, this, hx]
        · by_cases s3 : s = y
          · subst s3; simp [s1, s2, hy]
          · simp [s1, s2, s3]
    have hpk : pkF (extF G) 34 = 16 ^ z.val + (2 * 16 ^ x.val + 2 * 16 ^ y.val) := by
      simp only [G]
      rw [pk_add_counts, pk_add_counts, pk_indicator, pk_indicator, pk_indicator]
      omega
    have := hasCode_mono tree hv _ _ _ hc
      (by rw [← hpk]; exact small_hand G (fun s => Nat.le_trans (hGH s) (hH.2 s)))
      (small_hand H hH.2)
      (by rw [← hpk]; exact sub_fld G H hGH hH.2)
    unfold Covered; rw [hw]; exact this
  rcases Nat.lt_or_gt_of_ne (fun e => hab (Fin.ext e)) with h | h
  · exact key a b haP hbP haz hbz h hgab
  · exact key b a hbP haP hbz haz h hgab.symm

end Tenpai
