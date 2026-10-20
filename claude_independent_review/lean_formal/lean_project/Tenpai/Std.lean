import Tenpai.Melds
import Tenpai.Loops

/-!
# Standard-form waits in terms of per-category information

For a hand `H` let `u k` be the packed vector of category `k`.  Then
`t ∈ W_std(H)` iff `H t < 4` and either
* category `x = cat t` becomes "pair + melds" after adding `t`, and all other categories are
  "melds", or
* category `x` becomes "melds" after adding `t`, some other category `y` is "pair + melds",
  and the remaining categories are "melds".
-/

namespace Tenpai

/-! ## per-category tests -/

noncomputable def cM (k v : Nat) : Bool := isM (catLen k) (catLim k) v
noncomputable def cP (k v : Nat) : Bool := isP (catLen k) (catLim k) v
noncomputable def cWM (k v : Nat) : Nat := wmL (catLen k) (catLim k) v
noncomputable def cWP (k v : Nat) : Nat := wpL (catLen k) (catLim k) v

theorem shiftLeft_four (a q : Nat) : Nat.shiftLeft a (Nat.mul 4 q) = a * 16 ^ q := by
  show a <<< (4 * q) = a * 16 ^ q
  rw [Nat.shiftLeft_eq, Nat.pow_mul]

theorem isP_iff (len lim v : Nat) :
    isP len lim v = true ↔ ∃ q < len, 2 ≤ fld v q ∧ isM len lim (v - 2 * 16 ^ q) = true := by
  unfold isP
  rw [anyBelow_iff]
  apply exists_congr; intro q
  apply and_congr_right; intro _
  rw [Bool.and_eq_true, force_eq, shiftLeft_four]
  simp only [Nat.ble_eq]
  rfl

theorem testBit_wmL (len lim v t : Nat) :
    (wmL len lim v).testBit t = true ↔ t < len ∧ fld v t < 4 ∧ isM len lim (v + 16 ^ t) = true := by
  unfold wmL
  rw [testBit_maskBelow, Bool.and_eq_true, decide_eq_true_iff, Bool.and_eq_true, force_eq,
    shiftLeft_four, Nat.one_mul]
  simp only [Nat.blt_eq]
  rfl

theorem testBit_wpL (len lim v t : Nat) :
    (wpL len lim v).testBit t = true ↔ t < len ∧ fld v t < 4 ∧ isP len lim (v + 16 ^ t) = true := by
  unfold wpL
  rw [testBit_maskBelow, Bool.and_eq_true, decide_eq_true_iff, Bool.and_eq_true, force_eq,
    shiftLeft_four, Nat.one_mul]
  simp only [Nat.blt_eq]
  rfl

/-! ## totals -/

theorem sum_map_add {α : Type} (L : List α) (f g : α → Nat) :
    (L.map (fun s => f s + g s)).sum = (L.map f).sum + (L.map g).sum := by
  induction L with
  | nil => rfl
  | cons a L ih => simp only [List.map_cons, List.sum_cons, ih]; omega

theorem sum_map_indicator (p : Tile) (c : Nat) (L : List Tile) (hL : L.Nodup) :
    (L.map (fun s => if s = p then c else 0)).sum = if p ∈ L then c else 0 := by
  induction L with
  | nil => simp
  | cons a L ih =>
    rw [List.nodup_cons] at hL
    simp only [List.map_cons, List.sum_cons, ih hL.2, List.mem_cons]
    by_cases ha : a = p
    · subst ha; simp [hL.1]
    · simp only [ha, ite_false, Nat.zero_add]
      by_cases hp : p ∈ L
      · simp [hp]
      · simp [hp, show ¬ p = a from fun e => ha e.symm]

theorem total_add (f g : Counts) : total (fun s => f s + g s) = total f + total g := by
  unfold total; exact sum_map_add _ f g

theorem total_indicator (p : Tile) (c : Nat) : total (fun s => if s = p then c else 0) = c := by
  unfold total
  rw [sum_map_indicator p c _ (List.nodup_finRange 34)]
  simp [List.mem_finRange]

theorem total_congr {f g : Counts} (h : ∀ s, f s = g s) : total f = total g := by
  have : f = g := funext h
  subst this; rfl

theorem total_meld (m : Meld) (hv : m.Valid) : total m.count = 3 := by
  cases m with
  | trip x =>
    have : (Meld.trip x).count = fun s => if s = x then 3 else 0 := by funext s; rfl
    rw [this, total_indicator]
  | seq x =>
    have hv' : x.val < 27 ∧ x.val % 9 ≤ 6 := hv
    let x1 : Tile := ⟨x.val + 1, by omega⟩
    let x2 : Tile := ⟨x.val + 2, by omega⟩
    have : (Meld.seq x).count = fun s =>
        (fun s => (if s = x then 1 else 0) + (if s = x1 then 1 else 0)) s + (if s = x2 then 1 else 0) := by
      funext s
      simp only [Meld.count, Fin.ext_iff, x1, x2]
      repeat' split
      all_goals omega
    rw [this, total_add, total_add, total_indicator, total_indicator, total_indicator]

theorem total_mcount (ms : List Meld) (hv : ∀ m ∈ ms, m.Valid) : total (mcount ms) = 3 * ms.length := by
  induction ms with
  | nil =>
    have : mcount [] = fun _ => 0 := funext fun _ => rfl
    rw [this]; rfl
  | cons m ms ih =>
    have : mcount (m :: ms) = fun s => m.count s + mcount ms s := by
      funext s; simp [mcount]
    rw [this, total_add, total_meld m (hv m List.mem_cons_self),
      ih (fun m' h => hv m' (List.mem_cons_of_mem _ h))]
    simp; omega

/-! ## standard form = pair + melds -/

/-- remove a pair of `p` -/
def subPair (G : Counts) (p : Tile) : Counts := fun s => if s = p then G s - 2 else G s

theorem isStandard_iff (G : Counts) (hG : total G = 14) :
    IsStandard G ↔ ∃ p : Tile, 2 ≤ G p ∧ MeldDec (subPair G p) := by
  constructor
  · rintro ⟨p, m₁, m₂, m₃, m₄, h₁, h₂, h₃, h₄, he⟩
    refine ⟨p, by rw [he p]; simp; omega, [m₁, m₂, m₃, m₄], ?_, ?_⟩
    · intro m hm
      simp only [List.mem_cons, List.not_mem_nil, or_false] at hm
      rcases hm with rfl | rfl | rfl | rfl <;> assumption
    · intro s
      simp only [subPair, mcount, List.map_cons, List.map_nil, List.sum_cons, List.sum_nil, he s]
      split <;> simp_all <;> omega
  · rintro ⟨p, hp, ms, hv, he⟩
    have htot : total (mcount ms) = 12 := by
      have h1 : total G = total (fun s => mcount ms s + (if s = p then 2 else 0)) := by
        apply total_congr; intro s
        have := he s
        simp only [subPair] at this
        split at this
        · next h => subst h; simp; omega
        · next h => simp [h]; omega
      rw [total_add, total_indicator] at h1
      have : total (fun s => mcount ms s) = total (mcount ms) := rfl
      omega
    rw [total_mcount ms hv] at htot
    have hlen : ms.length = 4 := by omega
    match ms, hlen with
    | [m₁, m₂, m₃, m₄], _ =>
      refine ⟨p, m₁, m₂, m₃, m₄, hv _ (by simp), hv _ (by simp), hv _ (by simp), hv _ (by simp), ?_⟩
      intro s
      have := he s
      simp only [subPair, mcount, List.map_cons, List.map_nil, List.sum_cons, List.sum_nil] at this
      split at this
      · next h => subst h; simp; omega
      · next h => simp [h]; omega

/-! ## packed category vectors of modified hands -/

theorem extF_lt (F : Counts) (hF : ∀ s, F s ≤ 4) (t : Nat) : extF F t < 16 := by
  unfold extF; split
  · have := hF ⟨t, by assumption⟩; omega
  · omega

theorem catF_lt (F : Counts) (hF : ∀ s, F s ≤ 4) (k j : Nat) : catF (extF F) k j < 16 :=
  extF_lt F hF _

theorem catLen_le (k : Nat) (hk : k < 4) (j : Nat) (hj : j < catLen k) : 9 * k + j < 34 := by
  unfold catLen at hj; split at hj <;> omega

/-- the packed category vector of a tile `t` (field `t % 9` of category `t / 9`) -/
theorem fld_catPk (F : Counts) (hF : ∀ s, F s ≤ 4) (t : Tile) :
    fld (catPk (extF F) (t.val / 9)) (t.val % 9) = F t := by
  have ht := t.isLt
  unfold catPk
  rw [fld_pkF _ _ (fun i _ => catF_lt F hF _ _), ite_eq_left (by unfold catLen; split <;> omega)]
  simp only [catF, extF, show 9 * (t.val / 9) + t.val % 9 = t.val by omega, ht, dite_true]

theorem catPk_addTile (H : Counts) (_hH : ∀ s, H s ≤ 4) (t : Tile) (_ht : H t < 4) (k : Nat) :
    catPk (extF (addTile H t)) k =
      if k = t.val / 9 then catPk (extF H) k + 16 ^ (t.val % 9) else catPk (extF H) k := by
  have htl := t.isLt
  unfold catPk
  by_cases hk : k = t.val / 9
  · rw [ite_eq_left hk]
    have hj : t.val % 9 < catLen k := by unfold catLen; split <;> omega
    rw [pkF_add_single _ _ _ hj]
    apply pkF_congr
    intro i hi
    simp only [catF, extF, addTile]
    by_cases hi' : i = t.val % 9
    · subst hi'
      rw [ite_eq_left rfl]
      have e : 9 * k + t.val % 9 = t.val := by omega
      simp only [e, htl, dite_true, ite_true]
    · rw [ite_eq_right hi']
      have hlt := catLen_le k (by omega) i hi
      simp only [hlt, dite_true]
      rw [ite_eq_right]
      intro e
      have := congrArg Fin.val e
      simp only at this
      omega
  · rw [ite_eq_right hk]
    apply pkF_congr
    intro i hi
    simp only [catF, extF, addTile]
    split
    · next hlt =>
      rw [ite_eq_right]
      intro e
      have := congrArg Fin.val e
      simp only at this
      have := (inCat_iff k t.val (by unfold catLen at hi; split at hi <;> omega) htl).mp ⟨by omega, by omega⟩
      exact hk this.symm
    · rfl

theorem catPk_subPair (G : Counts) (p : Tile) (hp : 2 ≤ G p) (k : Nat) :
    catPk (extF (subPair G p)) k =
      if k = p.val / 9 then catPk (extF G) k - 2 * 16 ^ (p.val % 9) else catPk (extF G) k := by
  have hpl := p.isLt
  unfold catPk
  by_cases hk : k = p.val / 9
  · rw [ite_eq_left hk]
    have hj : p.val % 9 < catLen k := by unfold catLen; split <;> omega
    have hge : 2 ≤ catF (extF G) k (p.val % 9) := by
      simp only [catF, extF, show 9 * k + p.val % 9 = p.val by omega, hpl, dite_true]; exact hp
    rw [pkF_sub_pair _ _ _ hj hge]
    apply pkF_congr
    intro i hi
    simp only [catF, extF, subPair]
    by_cases hi' : i = p.val % 9
    · subst hi'
      rw [ite_eq_left rfl]
      simp only [show 9 * k + p.val % 9 = p.val by omega, hpl, dite_true, ite_true]
    · rw [ite_eq_right hi']
      have hlt := catLen_le k (by omega) i hi
      simp only [hlt, dite_true]
      rw [ite_eq_right]
      intro e
      have := congrArg Fin.val e
      simp only at this
      omega
  · rw [ite_eq_right hk]
    apply pkF_congr
    intro i hi
    simp only [catF, extF, subPair]
    split
    · next hlt =>
      rw [ite_eq_right]
      intro e
      have := congrArg Fin.val e
      simp only at this
      have := (inCat_iff k p.val (by unfold catLen at hi; split at hi <;> omega) hpl).mp ⟨by omega, by omega⟩
      exact hk this.symm
    · rfl

/-! ## pair + melds via the per-category tests -/

theorem subPair_le (G : Counts) (hG : ∀ s, G s ≤ 4) (p : Tile) : ∀ s, subPair G p s ≤ 4 := by
  intro s; unfold subPair; split <;> have := hG s <;> omega

/-- `∃ p, 2 ≤ G p ∧ G - {p,p}` splits into melds, category by category -/
theorem pairMelds_iff (G : Counts) (hG : ∀ s, G s ≤ 4) :
    (∃ p : Tile, 2 ≤ G p ∧ MeldDec (subPair G p)) ↔
      ∃ z < 4, cP z (catPk (extF G) z) = true ∧ ∀ k < 4, k ≠ z → cM k (catPk (extF G) k) = true := by
  constructor
  · rintro ⟨p, hp, hd⟩
    rw [meldDec_iff_isM _ (fun s => by have := subPair_le G hG p s; omega)] at hd
    have hpl := p.isLt
    refine ⟨p.val / 9, by omega, ?_, ?_⟩
    · unfold cP
      rw [isP_iff]
      refine ⟨p.val % 9, by unfold catLen; split <;> omega, ?_, ?_⟩
      · rw [fld_catPk G hG p]; exact hp
      · have := hd (p.val / 9) (by omega)
        rw [catPk_subPair G p hp, ite_eq_left rfl] at this
        exact this
    · intro k hk hne
      have := hd k hk
      rw [catPk_subPair G p hp, ite_eq_right hne] at this
      exact this
  · rintro ⟨z, hz, hP, hM⟩
    unfold cP at hP
    rw [isP_iff] at hP
    obtain ⟨q, hq, h2, hm⟩ := hP
    have hzq := catLen_le z hz q hq
    let p : Tile := ⟨9 * z + q, hzq⟩
    have hpz : p.val / 9 = z := by
      show (9 * z + q) / 9 = z; unfold catLen at hq; split at hq <;> omega
    have hpq : p.val % 9 = q := by
      show (9 * z + q) % 9 = q; unfold catLen at hq; split at hq <;> omega
    have hGp : 2 ≤ G p := by
      have := fld_catPk G hG p
      rw [hpz, hpq] at this
      omega
    refine ⟨p, hGp, ?_⟩
    rw [meldDec_iff_isM _ (fun s => by have := subPair_le G hG p s; omega)]
    intro k hk
    rw [catPk_subPair G p hGp]
    split
    · next hkz =>
      rw [hpz] at hkz; subst hkz; rw [hpq]; exact hm
    · next hkz =>
      rw [hpz] at hkz
      exact hM k hk hkz

/-! ## the standard-form wait criterion -/

theorem total_addTile (H : Counts) (t : Tile) : total (addTile H t) = total H + 1 := by
  have : addTile H t = fun s => H s + (if s = t then 1 else 0) := by
    funext s; simp only [addTile]; split <;> simp_all
  rw [this, total_add, total_indicator]

theorem addTile_le (H : Counts) (hH : ∀ s, H s ≤ 4) (t : Tile) (ht : H t < 4) : ∀ s, addTile H t s ≤ 4 := by
  intro s; unfold addTile; split
  · next h => subst h; omega
  · exact hH s

/-- **standard-form waits through the per-category tests** -/
theorem std_wait_iff (H : Counts) (hH : IsHand H) (t : Tile) (ht : H t < 4) :
    IsStandard (addTile H t) ↔
      (cP (t.val / 9) (catPk (extF H) (t.val / 9) + 16 ^ (t.val % 9)) = true ∧
          ∀ k < 4, k ≠ t.val / 9 → cM k (catPk (extF H) k) = true) ∨
      (cM (t.val / 9) (catPk (extF H) (t.val / 9) + 16 ^ (t.val % 9)) = true ∧
          ∃ y < 4, y ≠ t.val / 9 ∧ cP y (catPk (extF H) y) = true ∧
            ∀ k < 4, k ≠ t.val / 9 → k ≠ y → cM k (catPk (extF H) k) = true) := by
  have hle := addTile_le H hH.2 t ht
  rw [isStandard_iff _ (by rw [total_addTile, hH.1]), pairMelds_iff _ hle]
  have htl := t.isLt
  have hx : t.val / 9 < 4 := by omega
  simp only [catPk_addTile H hH.2 t ht]
  constructor
  · rintro ⟨z, hz, hP, hM⟩
    by_cases hzx : z = t.val / 9
    · subst hzx
      left
      rw [ite_eq_left rfl] at hP
      refine ⟨hP, fun k hk hne => ?_⟩
      have := hM k hk hne
      rw [ite_eq_right hne] at this
      exact this
    · right
      rw [ite_eq_right hzx] at hP
      have hMx := hM (t.val / 9) hx (fun e => hzx e.symm)
      rw [ite_eq_left rfl] at hMx
      refine ⟨hMx, z, hz, hzx, hP, fun k hk h1 h2 => ?_⟩
      have := hM k hk h2
      rw [ite_eq_right h1] at this
      exact this
  · rintro (⟨hP, hM⟩ | ⟨hMx, y, hy, hyx, hP, hM⟩)
    · refine ⟨t.val / 9, hx, by rw [ite_eq_left rfl]; exact hP, fun k hk hne => ?_⟩
      rw [ite_eq_right hne]; exact hM k hk hne
    · refine ⟨y, hy, by rw [ite_eq_right hyx]; exact hP, fun k hk hne => ?_⟩
      by_cases hkx : k = t.val / 9
      · rw [ite_eq_left hkx]; subst hkx; exact hMx
      · rw [ite_eq_right hkx]; exact hM k hk hkx hne

end Tenpai
