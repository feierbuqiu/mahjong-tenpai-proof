import Tenpai.Shape
import Tenpai.Checks

/-! # What the kernel checks mean -/

namespace Tenpai

/-! ## packed vectors with small fields -/

/-- reconstruction: a number below `16^n` is the packing of its own fields -/
theorem pkF_fld (x n : Nat) (hx : x < 16 ^ n) : pkF (fld x) n = x := by
  apply eq_of_fld_eq
  intro q
  rw [fld_pkF _ _ (fun i _ => by rw [fld_eq]; exact Nat.mod_lt _ (by omega))]
  split
  · rfl
  · next hq =>
    rw [fld_eq, Nat.div_eq_of_lt (Nat.lt_of_lt_of_le hx (Nat.pow_le_pow_right (by omega) (by omega)))]

/-- `fits` on any two vectors below `16^34` whose fields are at most 4 -/
theorem fits_iff' (c h : Nat) (hc : c < 16 ^ 34) (hh : h < 16 ^ 34)
    (hc4 : ∀ t < 34, fld c t ≤ 4) (hh4 : ∀ t < 34, fld h t ≤ 4) :
    fits c h = true ↔ ∀ t < 34, fld c t ≤ fld h t := by
  have e1 := pkF_fld c 34 hc
  have e2 := pkF_fld h 34 hh
  have := fits_iff (fld c) (fld h) hc4 hh4
  rw [e1, e2] at this
  exact this

theorem fits_mono (c h h' : Nat) (hc : c < 16 ^ 34) (hh : h < 16 ^ 34) (hh' : h' < 16 ^ 34)
    (hc4 : ∀ t < 34, fld c t ≤ 4) (hh4 : ∀ t < 34, fld h t ≤ 4) (hh4' : ∀ t < 34, fld h' t ≤ 4)
    (hle : ∀ t < 34, fld h t ≤ fld h' t) (hf : fits c h = true) : fits c h' = true := by
  rw [fits_iff' c h' hc hh' hc4 hh4']
  rw [fits_iff' c h hc hh hc4 hh4] at hf
  intro t ht; exact Nat.le_trans (hf t ht) (hle t ht)

/-! ## codes -/

/-- the multiplicity function of a code -/
def codeCnt (e : Nat) (t : Nat) : Nat :=
  (if codeTile e 0 = t then 1 else 0) + (if codeTile e 1 = t then 1 else 0) +
  (if codeTile e 2 = t then 1 else 0) + (if codeTile e 3 = t then 1 else 0)

theorem validCode_iff (e : Nat) : validCode e = true ↔
    e < 16777216 ∧ codeTile e 0 < 34 ∧ codeTile e 1 < 34 ∧ codeTile e 2 < 34 ∧ codeTile e 3 < 34 := by
  unfold validCode
  simp only [Bool.and_eq_true, Nat.blt_eq]
  constructor
  · rintro ⟨⟨⟨⟨h0, h1⟩, h2⟩, h3⟩, h4⟩; exact ⟨h0, h1, h2, h3, h4⟩
  · rintro ⟨h0, h1, h2, h3, h4⟩; exact ⟨⟨⟨⟨h0, h1⟩, h2⟩, h3⟩, h4⟩

theorem codeVec_eq (e : Nat) (he : validCode e = true) : codeVec e = pkF (codeCnt e) 34 := by
  rw [validCode_iff] at he
  obtain ⟨-, h0, h1, h2, h3⟩ := he
  have u : ∀ i, Nat.shiftLeft 1 (Nat.mul 4 i) = 16 ^ i := fun i => by
    rw [shiftLeft_four, Nat.one_mul]
  unfold codeVec
  rw [u, u, u, u]
  show 16 ^ codeTile e 0 + 16 ^ codeTile e 1 + (16 ^ codeTile e 2 + 16 ^ codeTile e 3) = _
  rw [← pkF_single _ 34 h0, ← pkF_single _ 34 h1, ← pkF_single _ 34 h2, ← pkF_single _ 34 h3,
    ← pkF_add, ← pkF_add, ← pkF_add]
  apply pkF_congr
  intro j _
  unfold codeCnt
  simp only [eq_comm (a := codeTile e _)]
  omega

theorem codeCnt_le (e t : Nat) : codeCnt e t ≤ 4 := by
  unfold codeCnt; split <;> split <;> split <;> split <;> omega

theorem codeVec_lt (e : Nat) (he : validCode e = true) : codeVec e < 16 ^ 34 := by
  rw [codeVec_eq e he]; exact pkF_lt _ _ (fun j _ => by have := codeCnt_le e j; omega)

theorem fld_codeVec (e : Nat) (he : validCode e = true) (t : Nat) (ht : t < 34) :
    fld (codeVec e) t = codeCnt e t := by
  rw [codeVec_eq e he, fld_pkF _ _ (fun j _ => by have := codeCnt_le e j; omega), ite_eq_left ht]

/-! ## hands as packed vectors -/

theorem hand_lt (H : Counts) (hH : ∀ s, H s ≤ 4) : pkF (extF H) 34 < 16 ^ 34 :=
  pkF_lt _ _ (fun j _ => extF_lt H hH j)

theorem hand_fld4 (H : Counts) (hH : ∀ s, H s ≤ 4) (t : Nat) (ht : t < 34) : fld (pkF (extF H) 34) t ≤ 4 := by
  rw [fld_hand H hH]; simp only [extF, ht, dite_true]; exact hH _

/-! ## the plan -/

theorem classCodes_eq (tree : PTree (List Nat)) (W : Nat) : classCodes tree W = tree.find [] W := by
  unfold classCodes; rw [force_eq]

theorem mem_classCodes (tree : PTree (List Nat)) (W e : Nat) (h : e ∈ classCodes tree W) :
    ∃ cs, (W, cs) ∈ tree.toList ∧ e ∈ cs := by
  rw [classCodes_eq] at h
  rcases PTree.find_mem [] tree W with h' | h'
  · rw [h'] at h; simp at h
  · exact ⟨_, h', h⟩

theorem hasCode_sound (tree : PTree (List Nat)) (W h : Nat) (hc : hasCode tree W h = true) :
    ∃ e ∈ classCodes tree W, fits (codeVec e) h = true :=
  (anyL_iff _ _).mp hc

/-- decoding: a code determines its class -/
theorem decode_sound (tree : PTree (List Nat)) (dtree : PTree Nat) (hd : decodeOK tree dtree = true)
    (W e : Nat) (he : e ∈ classCodes tree W) : dtree.find 0 e = W ∧ validCode e = true := by
  obtain ⟨cs, hmem, hecs⟩ := mem_classCodes tree W e he
  have := (allL_iff _ _).mp hd _ hmem
  have := (allL_iff _ _).mp this e hecs
  simp only [Bool.and_eq_true, Nat.beq_eq] at this
  exact this

/-! ## melds -/

/-- the packed vector of a meld -/
def meldPk : Meld → Nat
  | .trip x => tripV x.val
  | .seq x => seqV x.val

theorem unitV_eq (t : Nat) : unitV t = 16 ^ t := by
  unfold unitV; rw [shiftLeft_four, Nat.one_mul]

theorem meldPk_eq (m : Meld) (hm : m.Valid) : meldPk m = pkF (extF m.count) 34 := by
  cases m with
  | trip x =>
    show Nat.mul 3 (unitV x.val) = _
    rw [unitV_eq, ← pkF_single _ 34 x.isLt]
    show 3 * pkF _ 34 = _
    rw [← pkF_mul_const]
    apply pkF_congr
    intro j hj
    simp only [extF, hj, dite_true, Meld.count, Fin.ext_iff]
    split <;> simp_all
  | seq x =>
    have hv : x.val < 27 ∧ x.val % 9 ≤ 6 := hm
    show Nat.add (unitV x.val) (Nat.add (unitV (x.val + 1)) (unitV (x.val + 2))) = _
    rw [unitV_eq, unitV_eq, unitV_eq, ← pkF_single _ 34 x.isLt, ← pkF_single (x.val + 1) 34 (by omega),
      ← pkF_single (x.val + 2) 34 (by omega)]
    simp only [Nat.add_eq]
    rw [← pkF_add, ← pkF_add]
    apply pkF_congr
    intro j hj
    simp only [extF, hj, dite_true, Meld.count]
    repeat' split
    all_goals omega

/-- the starting tile of a meld -/
def Meld.tile : Meld → Tile
  | .trip x => x
  | .seq x => x

theorem mem_meldList (cats : Nat) (m : Meld) (hm : m.Valid) (hc : cats.testBit (m.tile.val / 9) = true) :
    meldPk m ∈ meldList cats := by
  unfold meldList
  rw [List.mem_flatMap]
  refine ⟨m.tile.val, List.mem_range.mpr m.tile.isLt, ?_⟩
  have hc' : Nat.testBit cats (Nat.div m.tile.val 9) = true := hc
  rw [hc', Bool.cond_true]
  cases m with
  | trip x => exact List.mem_cons_self
  | seq x =>
    have hv : x.val < 27 ∧ x.val % 9 ≤ 6 := hm
    have : seqOK x.val = true := by
      unfold seqOK; simp only [Bool.and_eq_true, Nat.blt_eq, Nat.ble_eq]; exact hv
    show seqV x.val ∈ tripV x.val :: cond (seqOK x.val) [seqV x.val] []
    rw [this]; simp

end Tenpai
