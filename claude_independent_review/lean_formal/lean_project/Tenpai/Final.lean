import Tenpai.Cover4
import Tenpai.Lower

/-!
# From the checks to `k* = 4`

* `feasible_four`: if all checks passed, the plan gives an encoder `f : ℋ → T⁴`
  (choose a code of the hand's class contained in the hand) whose codes determine the class
  (the decoding table).
* `kstar_of_checks`: together with the lower-bound witnesses, `k* = 4`.
-/

namespace Tenpai

/-- the ordered tuple of an encoded code -/
def tupleOf (e : Nat) : Fin 4 → Tile := fun i => ⟨codeTile e i.val % 34, Nat.mod_lt _ (by decide)⟩

theorem codeTile_eq (e i : Nat) : codeTile e i = e / 2 ^ (6 * i) % 64 := by
  unfold codeTile
  show e >>> (6 * i) % 64 = _
  rw [Nat.shiftRight_eq_div_pow]

theorem tupleOf_val (e : Nat) (he : validCode e = true) (i : Fin 4) : (tupleOf e i).val = codeTile e i.val := by
  rw [validCode_iff] at he
  show codeTile e i.val % 34 = codeTile e i.val
  apply Nat.mod_eq_of_lt
  rcases i with ⟨i, hi⟩
  rcases (show i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 3 by omega) with rfl | rfl | rfl | rfl
  · exact he.2.1
  · exact he.2.2.1
  · exact he.2.2.2.1
  · exact he.2.2.2.2

theorem tupleOf_inj (e e' : Nat) (he : validCode e = true) (he' : validCode e' = true)
    (h : tupleOf e = tupleOf e') : e = e' := by
  have hv : ∀ i : Fin 4, codeTile e i.val = codeTile e' i.val := fun i => by
    rw [← tupleOf_val e he i, ← tupleOf_val e' he' i, h]
  have h0 := hv 0; have h1 := hv 1; have h2 := hv 2; have h3 := hv 3
  simp only [codeTile_eq] at h0 h1 h2 h3
  have b := ((validCode_iff e).mp he).1
  have b' := ((validCode_iff e').mp he').1
  simp only [Fin.val_zero, Fin.val_one, Fin.val_two, show ((3 : Fin 4) : Nat) = 3 from rfl,
    Nat.mul_zero, Nat.pow_zero, Nat.div_one, Nat.mul_one,
    show 2 ^ 6 = 64 from rfl, show 2 ^ (6 * 2) = 4096 from rfl, show 2 ^ (6 * 3) = 262144 from rfl] at h0 h1 h2 h3
  omega

theorem countP_finRange4 (p : Fin 4 → Bool) :
    (List.finRange 4).countP p = (if p 0 then 1 else 0) + (if p 1 then 1 else 0) + (if p 2 then 1 else 0) +
      (if p 3 then 1 else 0) := by
  have : List.finRange 4 = [0, 1, 2, 3] := by decide
  rw [this]
  simp only [List.countP_cons, List.countP_nil]
  omega

theorem admissible_of_fits (H : Counts) (hH : ∀ s, H s ≤ 4) (e : Nat) (he : validCode e = true)
    (hf : fits (codeVec e) (pkF (extF H) 34) = true) : Admissible H (tupleOf e) := by
  intro t
  rw [fits_iff' _ _ (codeVec_lt e he) (hand_lt H hH)
    (fun t ht => by rw [fld_codeVec e he t ht]; exact codeCnt_le e t) (hand_fld4 H hH)] at hf
  have h := hf t.val t.isLt
  rw [fld_codeVec e he t.val t.isLt, fld_hand H hH] at h
  simp only [extF, t.isLt, dite_true] at h
  rw [countP_finRange4]
  have dec : ∀ i : Fin 4, decide (tupleOf e i = t) = decide (codeTile e i.val = t.val) := by
    intro i
    by_cases h : tupleOf e i = t
    · have : codeTile e i.val = t.val := by rw [← tupleOf_val e he i, h]
      simp [h, this]
    · have : ¬ codeTile e i.val = t.val := fun h' => h (Fin.ext (by rw [tupleOf_val e he i, h']))
      simp [h, this]
  rw [dec 0, dec 1, dec 2, dec 3]
  unfold codeCnt at h
  simp only [decide_eq_true_eq]
  exact h

/-- **k = 4 is feasible**, given the checks -/
theorem feasible_four (tree : PTree (List Nat)) (dtree : PTree Nat) (cuts : Nat → List Nat)
    (hc : Checked tree cuts) (hd : decodeOK tree dtree = true) : Feasible 4 := by
  have hcov : ∀ H : {H // InH H}, Covered tree H.1 := fun H => cover tree cuts hc H.1 H.2
  let code : {H // InH H} → Nat := fun H => Classical.choose (hcov H)
  have hspec : ∀ H, code H ∈ classCodes tree (wAll (cvOf H.1)) ∧
      fits (codeVec (code H)) (pkF (extF H.1) 34) = true := fun H => by
    have := Classical.choose_spec (hcov H)
    exact ⟨this.1, this.2⟩
  have hval : ∀ H, validCode (code H) = true := fun H => hc.valid _ _ (hspec H).1
  refine ⟨fun H => tupleOf (code H), fun H => admissible_of_fits H.1 H.2.1.2 _ (hval H) (hspec H).2, ?_⟩
  intro H H' hf
  have he := tupleOf_inj _ _ (hval H) (hval H') hf
  have d1 := (decode_sound tree dtree hd _ _ (hspec H).1).1
  have d2 := (decode_sound tree dtree hd _ _ (hspec H').1).1
  rw [he] at d1
  have hm : wAll (cvOf H.1) = wAll (cvOf H'.1) := d1.symm.trans d2
  funext t
  apply propext
  rw [← wAll_correct H.1 H.2.1 t, ← wAll_correct H'.1 H'.2.1 t, hm]

/-- **k* = 4**, given the checks and the lower-bound witnesses -/
theorem kstar_of_checks (tree : PTree (List Nat)) (dtree : PTree Nat) (cuts : Nat → List Nat) (ws : List Nat)
    (hc : Checked tree cuts) (hd : decodeOK tree dtree = true) (hw : witOK ws = true) (hl : ws.length = 347) :
    IsKStar 4 := by
  refine ⟨by decide, feasible_four tree dtree cuts hc hd, fun k _ hk => ?_⟩
  exact Decidable.byContradiction fun hlt => not_feasible_le3 ws hw hl k (by omega) hk

end Tenpai
