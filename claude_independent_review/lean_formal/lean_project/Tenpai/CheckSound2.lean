import Tenpai.CheckSound

/-! # What the kernel checks mean (continued): T0–T4, K -/

namespace Tenpai

theorem shift_one (z : Nat) : Nat.shiftLeft 1 z = 2 ^ z := by
  show 1 <<< z = 2 ^ z; rw [Nat.one_shiftLeft]

/-- every code stored in the plan is four tiles `< 34` -/
def TreeValid (tree : PTree (List Nat)) : Prop := ∀ W e, e ∈ classCodes tree W → validCode e = true

theorem treeValid_of_decode (tree : PTree (List Nat)) (dtree : PTree Nat) (hd : decodeOK tree dtree = true) :
    TreeValid tree := fun W e he => (decode_sound tree dtree hd W e he).2

/-- a vector below `16^34` with all fields at most 4 -/
def Small (h : Nat) : Prop := h < 16 ^ 34 ∧ ∀ t < 34, fld h t ≤ 4

/-- `hasCode` is monotone in the hand -/
theorem hasCode_mono (tree : PTree (List Nat)) (hv : TreeValid tree) (W h h' : Nat)
    (hc : hasCode tree W h = true) (hs : Small h) (hs' : Small h') (hle : ∀ t < 34, fld h t ≤ fld h' t) :
    ∃ e ∈ classCodes tree W, fits (codeVec e) h' = true := by
  obtain ⟨e, he, hf⟩ := hasCode_sound tree W h hc
  have hve := hv W e he
  refine ⟨e, he, fits_mono _ h h' (codeVec_lt e hve) hs.1 hs'.1
    (fun t ht => by rw [fld_codeVec e hve t ht]; exact codeCnt_le e t) hs.2 hs'.2 hle hf⟩

theorem le4_iff (h : Nat) : le4 h = true ↔ ∀ t < 34, fld h t ≤ 4 := by
  unfold le4; rw [allBelow_iff]; simp [Nat.ble_eq]

/-! ## melds -/

theorem mem_meldList_iff (cats m : Nat) : m ∈ meldList cats ↔
    ∃ t < 34, cats.testBit (t / 9) = true ∧ (m = tripV t ∨ (seqOK t = true ∧ m = seqV t)) := by
  unfold meldList
  rw [List.mem_flatMap]
  constructor
  · rintro ⟨t, ht, hm⟩
    rw [List.mem_range] at ht
    cases hc : Nat.testBit cats (Nat.div t 9)
    · rw [hc, Bool.cond_false] at hm; simp at hm
    · rw [hc, Bool.cond_true] at hm
      refine ⟨t, ht, hc, ?_⟩
      cases hs : seqOK t
      · rw [hs, Bool.cond_false] at hm; simp at hm; exact Or.inl hm
      · rw [hs, Bool.cond_true] at hm; simp at hm
        rcases hm with h | h
        · exact Or.inl h
        · exact Or.inr ⟨rfl, h⟩
  · rintro ⟨t, ht, hc, hm⟩
    refine ⟨t, List.mem_range.mpr ht, ?_⟩
    have hc' : Nat.testBit cats (Nat.div t 9) = true := hc
    rw [hc', Bool.cond_true]
    rcases hm with h | ⟨hs, h⟩
    · subst h; exact List.mem_cons_self
    · subst h; rw [hs, Bool.cond_true]; simp

/-! ## T0 -/

theorem t0_sound (tree : PTree (List Nat)) (h : t0ok tree = true) (z : Nat) (hz : z < 34) (m : Nat)
    (hm : m ∈ meldList (catsExcept (z / 9))) : hasCode tree (2 ^ z) (16 ^ z + m) = true := by
  have := (allBelow_iff _ 34).mp h z hz
  have := (allL_iff _ _).mp this m hm
  rw [shift_one, unitV_eq] at this
  exact this

/-! ## the meld rule -/

theorem meldRule_sound (tree : PTree (List Nat)) (hv : TreeValid tree) (W A cats : Nat)
    (h : meldRule tree W A cats = true)
    (m1 m2 m3 : Nat) (h1 : m1 ∈ meldList cats) (h2 : m2 ∈ meldList cats) (h3 : m3 ∈ meldList cats)
    (hs : Small (A + m1 + m2 + m3))
    (hpart : ∀ i, i = m1 ∨ i = m2 ∨ i = m3 → Small (A + i) ∧ ∀ t < 34, fld (A + i) t ≤ fld (A + m1 + m2 + m3) t) :
    ∃ e ∈ classCodes tree W, fits (codeVec e) (A + m1 + m2 + m3) = true := by
  by_cases g : hasCode tree W (A + m1) = true ∨ hasCode tree W (A + m2) = true ∨ hasCode tree W (A + m3) = true
  · rcases g with g | g | g
    · exact hasCode_mono tree hv W _ _ g (hpart m1 (Or.inl rfl)).1 hs (hpart m1 (Or.inl rfl)).2
    · exact hasCode_mono tree hv W _ _ g (hpart m2 (Or.inr (Or.inl rfl))).1 hs (hpart m2 (Or.inr (Or.inl rfl))).2
    · exact hasCode_mono tree hv W _ _ g (hpart m3 (Or.inr (Or.inr rfl))).1 hs (hpart m3 (Or.inr (Or.inr rfl))).2
  · simp only [not_or, Bool.not_eq_true] at g
    obtain ⟨g1, g2, g3⟩ := g
    unfold meldRule at h
    have bad : ∀ i, (i ∈ meldList cats ∧ hasCode tree W (A + i) = false) →
        i ∈ (meldList cats).filter (fun m => !(hasCode tree W (Nat.add A m))) := fun i hi => by
      rw [List.mem_filter]; refine ⟨hi.1, ?_⟩; show (!(hasCode tree W (A + i))) = true; rw [hi.2]; rfl
    have := (allL_iff _ _).mp h m1 (bad m1 ⟨h1, g1⟩)
    have := (allL_iff _ _).mp this m2 (bad m2 ⟨h2, g2⟩)
    have := (allL_iff _ _).mp this m3 (bad m3 ⟨h3, g3⟩)
    rw [Bool.or_eq_true] at this
    rcases this with hl | hc
    · exfalso
      have : le4 (A + m1 + m2 + m3) = true := (le4_iff _).mpr hs.2
      simp only [Bool.not_eq_true'] at hl
      exact absurd this (by show ¬ (le4 (Nat.add (Nat.add (Nat.add A m1) m2) m3) = true); rw [hl]; simp)
    · exact hasCode_sound tree W _ hc

/-! ## T1 -/

theorem t1_sound (tree : PTree (List Nat)) (k n u : Nat) (h : t1unit tree k n u = true) :
    Nat.shiftLeft (cWP k u) (Nat.mul 9 k) = 0 ∨
    hasCode tree (Nat.shiftLeft (cWP k u) (Nat.mul 9 k)) (Nat.shiftLeft u (Nat.mul 36 k)) = true ∨
    (n = 4 ∧ meldRule tree (Nat.shiftLeft (cWP k u) (Nat.mul 9 k)) (Nat.shiftLeft u (Nat.mul 36 k)) (catsExcept k) = true) := by
  unfold t1unit at h
  rw [force_eq] at h
  simp only [Bool.or_eq_true, Bool.and_eq_true, Nat.beq_eq] at h
  rcases h with (h | h) | h
  · exact Or.inl h
  · exact Or.inr (Or.inl h)
  · exact Or.inr (Or.inr h)

/-! ## T2 -/

/-- what the T2 check establishes for one pair of category vectors -/
def T2unit (tree : PTree (List Nat)) (x y nx ny u v : Nat) : Prop :=
  let W := Nat.lor (cond (cP y v) (Nat.shiftLeft (cWM x u) (Nat.mul 9 x)) 0)
                   (cond (cP x u) (Nat.shiftLeft (cWM y v) (Nat.mul 9 y)) 0)
  W = 0 ∨ hasCode tree W (Nat.add (Nat.shiftLeft u (Nat.mul 36 x)) (Nat.shiftLeft v (Nat.mul 36 y))) = true ∨
    (nx + ny = 4 ∧ meldRule tree W (Nat.add (Nat.shiftLeft u (Nat.mul 36 x)) (Nat.shiftLeft v (Nat.mul 36 y)))
      (catsExcept2 x y) = true)

theorem infOf_eq (k w : Nat) : infOf k w = ⟨Nat.shiftLeft w (Nat.mul 36 k), cP k w, Nat.shiftLeft (cWM k w) (Nat.mul 9 k)⟩ := by
  unfold infOf; rw [force_eq, force_eq]

/-- one pair, from the `t2pair` test (or an irrelevant side) -/
theorem t2pair_unit (tree : PTree (List Nat)) (x y nx ny u v : Nat)
    (h : relevant (infOf x u) = false ∨ relevant (infOf y v) = false ∨
      t2pair tree (catsExcept2 x y) (Nat.add nx ny) (infOf x u) (infOf y v) = true) :
    T2unit tree x y nx ny u v := by
  unfold T2unit
  intro W
  have hW0 : relevant (infOf x u) = false ∨ relevant (infOf y v) = false → W = 0 := by
    intro hr
    simp only [W]
    rcases hr with hr | hr
    · rw [infOf_eq] at hr
      simp only [relevant, Bool.or_eq_false_iff, Bool.not_eq_false', Nat.beq_eq] at hr
      rw [hr.1, hr.2]
      apply Nat.eq_of_testBit_eq; intro i
      simp
    · rw [infOf_eq] at hr
      simp only [relevant, Bool.or_eq_false_iff, Bool.not_eq_false', Nat.beq_eq] at hr
      rw [hr.1, hr.2]
      apply Nat.eq_of_testBit_eq; intro i
      simp
  rcases h with hr | hr | hp
  · exact Or.inl (hW0 (Or.inl hr))
  · exact Or.inl (hW0 (Or.inr hr))
  · unfold t2pair at hp
    rw [force_eq, infOf_eq x u, infOf_eq y v] at hp
    simp only [Bool.or_eq_true, Bool.and_eq_true, Nat.beq_eq] at hp
    rcases hp with (hp | hp) | hp
    · exact Or.inl hp
    · exact Or.inr (Or.inl hp)
    · exact Or.inr (Or.inr ⟨hp.1, hp.2⟩)

theorem t2_sound (tree : PTree (List Nat)) (x y nx ny : Nat) (us : List Nat) (h : t2ok tree x y nx ny us = true)
    (u : Nat) (hu : u ∈ us) (v : Nat) (hvv : v ∈ vecs (catLen y) ny) : T2unit tree x y nx ny u v := by
  apply t2pair_unit
  have hu' := (allL_iff _ _).mp h u hu
  rw [Bool.or_eq_true] at hu'
  rcases hu' with hr | hall
  · exact Or.inl (by simpa using hr)
  · by_cases hry : relevant (infOf y v) = true
    · have hmem : infOf y v ∈ ((vecs (catLen y) ny).map (infOf y)).filter relevant :=
        List.mem_filter.mpr ⟨List.mem_map.mpr ⟨v, hvv, rfl⟩, hry⟩
      exact Or.inr (Or.inr ((allL_iff _ _).mp hall _ hmem))
    · exact Or.inr (Or.inl (by simpa using hry))

theorem t2rev_sound (tree : PTree (List Nat)) (x y nx ny : Nat) (vs : List Nat) (h : t2okRev tree x y nx ny vs = true)
    (v : Nat) (hv : v ∈ vs) (u : Nat) (huu : u ∈ vecs (catLen x) nx) : T2unit tree x y nx ny u v := by
  apply t2pair_unit
  have hv' := (allL_iff _ _).mp h v hv
  rw [Bool.or_eq_true] at hv'
  rcases hv' with hr | hall
  · exact Or.inr (Or.inl (by simpa using hr))
  · by_cases hrx : relevant (infOf x u) = true
    · have hmem : infOf x u ∈ ((vecs (catLen x) nx).map (infOf x)).filter relevant :=
        List.mem_filter.mpr ⟨List.mem_map.mpr ⟨u, huu, rfl⟩, hrx⟩
      exact Or.inr (Or.inr ((allL_iff _ _).mp hall _ hmem))
    · exact Or.inl (by simpa using hrx)

/-! ## T3 -/

theorem grpOf_le (cuts : List Nat) (t : Nat) : grpOf cuts t ≤ cuts.length := by
  unfold grpOf
  induction cuts with
  | nil => exact Nat.le_refl _
  | cons c cs ih =>
    show Nat.add (cond (Nat.ble c t) 1 0) (grpOf.countL (fun c => Nat.ble c t) cs) ≤ cs.length + 1
    have := ih
    cases Nat.ble c t <;> simp <;> omega

theorem t3_sound (tree : PTree (List Nat)) (cutsOf : Nat → List Nat) (h : t3ok tree cutsOf = true)
    (z : Nat) (hz : z < 34) :
    (∀ t, grpOf (cutsOf z) t ≤ 4) ∧
    ∀ x y, x < 34 → y < 34 → x < y → x ≠ z → y ≠ z → grpOf (cutsOf z) x = grpOf (cutsOf z) y →
      hasCode tree (2 ^ z) (16 ^ z + (2 * 16 ^ x + 2 * 16 ^ y)) = true := by
  have hz' := (allBelow_iff _ 34).mp h z hz
  rw [Bool.and_eq_true, Nat.ble_eq] at hz'
  refine ⟨fun t => Nat.le_trans (grpOf_le _ t) hz'.1, ?_⟩
  intro x y hx hy hxy hxz hyz hg
  have := (allBelow_iff _ 34).mp hz'.2 x hx
  have := (allBelow_iff _ 34).mp this y hy
  simp only [Bool.or_eq_true, Bool.not_eq_true', Nat.beq_eq] at this
  rcases this with (((h1 | h1) | h1) | h1) | h1
  · rw [Nat.blt_eq.mpr hxy] at h1; exact absurd h1 (by simp)
  · exact absurd h1 hxz
  · exact absurd h1 hyz
  · rw [hg, Nat.beq_refl] at h1; exact absurd h1 (by simp)
  · rw [shift_one, unitV_eq, unitV_eq, unitV_eq] at h1
    exact h1

/-! ## T4 -/

theorem forShapes_sound (p : (Nat → Nat) → Bool) (h : forShapes p = true) (n0 n1 n2 n3 : Nat)
    (h0 : n0 < 14) (h1 : n1 < 14) (h2 : n2 < 14) (hsum : n0 + n1 + n2 + n3 = 13) :
    p (sel4 n0 n1 n2 n3) = true := by
  have x := (allBelow_iff _ 14).mp h n0 h0
  have x := (allBelow_iff _ 14).mp x n1 h1
  have x := (allBelow_iff _ 14).mp x n2 h2
  have e3 : Nat.sub 13 (Nat.add n0 (Nat.add n1 n2)) = n3 := by
    show 13 - (n0 + (n1 + n2)) = n3; omega
  have hle : Nat.ble (Nat.add n0 (Nat.add n1 n2)) 13 = true := Nat.ble_eq.mpr (by show n0 + (n1 + n2) ≤ 13; omega)
  rw [e3, hle] at x
  simpa using x

theorem t4shape_sound (act : Nat → Bool) (n : Nat → Nat) (chk : (Nat → Nat) → Bool)
    (h : t4shape act n chk = true) (a b c d : Nat)
    (ha : a ∈ t4list (act 0) 0 (n 0)) (hb : b ∈ t4list (act 1) 1 (n 1))
    (hc : c ∈ t4list (act 2) 2 (n 2)) (hd : d ∈ t4list (act 3) 3 (n 3)) : chk (sel4 a b c d) = true := by
  unfold t4shape at h
  have x := (allL_iff _ _).mp h a ha
  have x := (allL_iff _ _).mp x b hb
  have x := (allL_iff _ _).mp x c hc
  exact (allL_iff _ _).mp x d hd

theorem t4A_sound (tree : PTree (List Nat)) (x : Nat) (h : t4okA tree x = true) (n0 n1 n2 n3 : Nat)
    (h0 : n0 < 14) (h1 : n1 < 14) (h2 : n2 < 14) (hsum : n0 + n1 + n2 + n3 = 13)
    (hs : shape1 x (sel4 n0 n1 n2 n3) = true) (a b c d : Nat)
    (ha : a ∈ t4list (Nat.beq 0 x) 0 n0) (hb : b ∈ t4list (Nat.beq 1 x) 1 n1)
    (hc : c ∈ t4list (Nat.beq 2 x) 2 n2) (hd : d ∈ t4list (Nat.beq 3 x) 3 n3) :
    t4handA tree x (sel4 a b c d) = true := by
  have := forShapes_sound _ h n0 n1 n2 n3 h0 h1 h2 hsum
  rw [hs] at this
  simp only [Bool.not_true, Bool.false_or] at this
  exact t4shape_sound _ _ _ this a b c d ha hb hc hd

theorem t4B_sound (tree : PTree (List Nat)) (x y : Nat) (h : t4okB tree x y = true) (n0 n1 n2 n3 : Nat)
    (h0 : n0 < 14) (h1 : n1 < 14) (h2 : n2 < 14) (hsum : n0 + n1 + n2 + n3 = 13)
    (hs : shape2 x y (sel4 n0 n1 n2 n3) = true) (a b c d : Nat)
    (ha : a ∈ t4list (Nat.beq 0 x || Nat.beq 0 y) 0 n0) (hb : b ∈ t4list (Nat.beq 1 x || Nat.beq 1 y) 1 n1)
    (hc : c ∈ t4list (Nat.beq 2 x || Nat.beq 2 y) 2 n2) (hd : d ∈ t4list (Nat.beq 3 x || Nat.beq 3 y) 3 n3) :
    t4handB tree x y (sel4 a b c d) = true := by
  have := forShapes_sound _ h n0 n1 n2 n3 h0 h1 h2 hsum
  rw [hs] at this
  simp only [Bool.not_true, Bool.false_or] at this
  exact t4shape_sound _ _ _ this a b c d ha hb hc hd

/-! ## K -/

theorem k_sound (tree : PTree (List Nat)) (h : kOK tree = true) (o t : Nat) (ho : o < 34) (ht : t < 34)
    (hoo : isOrphB o = true) (hto : isOrphB t = true) :
    hasCode tree (wAll (kokCv o t)) (glue (kokCv o t)) = true := by
  have x := (allBelow_iff _ 34).mp h o ho
  have x := (allBelow_iff _ 34).mp x t ht
  rw [hoo, hto] at x
  simpa using x

end Tenpai
