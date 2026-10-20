/-
  Mj.Bridge —— k=1 / k=2 / k=3 不可行的形式化否证（无 hbridge）

  统一论证（只看类数就已超过码池）:
    对 U 与 k, 取该类族的去重类键 keys; 每类取 S_C := P.codesOf W 中「长度 k 且元素 ⊆ U」的码。
    · 每类非空 (coversAll + 手牌 support ⊆ U + 码只含合法索引)
    · 键不同 ⇒ S_C 不交 (P.disjoint) ⇒ Σ|S_C| ≤ |U|^k (Mj.Lemma.budget / budgetNat)
    · 每类 ≥1 ⇒ Σ|S_C| ≥ keys.length = N
    · 若 |U|^k < N ⇒ ¬ ∃ P, P.lengths k ∧ P.coversAll k ∧ P.disjoint ∧ P.valid
  三例: (U = 前 9 张, k=1, N=387) / (同, k=2, N=387) / (U = u7N, k=3, N=347)。
  信任: 三条计数 N 由 native_decide 计算 (普查); 其余内核可检查。
  建模假设: Plan.valid —— 码只含合法牌索引 0..33 (协议语义: A 只能摆真实存在的牌)。
-/
import Mj.Basic
import Mj.Lemma
import Mj.Protocol
import Mj.Disproof

namespace Mj

open Hand

/-! ## 0. 通用去重（core/Std 无 nodup_eraseDups/Nodup.map，自证） -/

def dedupAux {α : Type} [BEq α] [LawfulBEq α] : List α → List α
  | [] => []
  | x :: t => if x ∈ dedupAux t then dedupAux t else x :: dedupAux t

theorem mem_dedupAux {α : Type} [BEq α] [LawfulBEq α] {x : α} :
    ∀ {l : List α}, x ∈ dedupAux l ↔ x ∈ l := by
  intro l
  induction l with
  | nil => simp [dedupAux]
  | cons a t ih =>
    rw [dedupAux]
    by_cases h : a ∈ dedupAux t
    · rw [if_pos h]
      constructor
      · intro hx; exact List.mem_cons_of_mem _ (ih.mp hx)
      · intro hx
        rcases List.mem_cons.mp hx with rfl | hx
        · exact h
        · exact ih.mpr hx
    · rw [if_neg h]
      constructor
      · intro hx
        rcases List.mem_cons.mp hx with rfl | hx
        · exact List.mem_cons_self
        · exact List.mem_cons_of_mem _ (ih.mp hx)
      · intro hx
        rcases List.mem_cons.mp hx with rfl | hx
        · exact List.mem_cons_self
        · exact List.mem_cons_of_mem _ (ih.mpr hx)

theorem dedupAux_nodup {α : Type} [BEq α] [LawfulBEq α] :
    ∀ l : List α, (dedupAux l).Nodup := by
  intro l
  induction l with
  | nil => simp [dedupAux]
  | cons a t ih =>
    rw [dedupAux]
    by_cases h : a ∈ dedupAux t
    · rw [if_pos h]; exact ih
    · rw [if_neg h, List.nodup_cons]; exact ⟨h, ih⟩

theorem eq_nil_of_dedupAux_eq_nil {α : Type} [BEq α] [LawfulBEq α] {l : List α}
    (h : dedupAux l = []) : l = [] := by
  cases l with
  | nil => rfl
  | cons a t =>
    have hmem : a ∈ dedupAux (a :: t) := by rw [mem_dedupAux]; exact List.mem_cons_self
    rw [h] at hmem
    exact absurd hmem (by simp)

theorem exists_mem_of_dedupAux_ne_nil {α : Type} [BEq α] [LawfulBEq α] {l : List α}
    (h : dedupAux l ≠ []) : ∃ x, x ∈ dedupAux l := by
  cases hd : dedupAux l with
  | nil => exact absurd hd h
  | cons a t => exact ⟨a, List.mem_cons_self⟩

/-! ## 1. 通用构造: U 内手牌与类键 -/

/-- 规范表: 所有码只含合法牌索引 0..33 -/
def Plan.valid (P : Plan) : Prop :=
  ∀ (W : List Nat) (c : Code), c ∈ P.codesOf W → ∀ x ∈ c, x < 34

/-- HandContains 可判定（用于计算） -/
instance (H : Hand) (c : Code) : Decidable (HandContains H c) := by
  unfold HandContains; infer_instance

/-- 手牌 support 全在 U 内 -/
def inU (U : List Nat) (H : Hand) : Bool :=
  (List.finRange 34).all (fun t => decide (H.get t = 0 ∨ t.val ∈ U))

theorem inU_get {U : List Nat} {H : Hand} (h : inU U H = true) {t : Tile} (ht : H.get t > 0) :
    t.val ∈ U := by
  have h1 := List.all_eq_true.mp h t (List.mem_finRange t)
  rcases of_decide_eq_true h1 with h2 | h2
  · omega
  · exact h2

/-- U 内、13 张、听牌的手牌 -/
def handSet (U : List Nat) (src : List Hand) : List Hand :=
  src.filter (fun H => inU U H && (H.total == 13) && !(waits H).isEmpty)

theorem mem_handSet {U : List Nat} {src : List Hand} {H : Hand} :
    H ∈ handSet U src ↔ H ∈ src ∧ (inU U H = true ∧ H.total = 13) ∧ waits H ≠ [] := by
  simp [handSet, List.mem_filter, Bool.and_eq_true, beq_iff_eq]

/-- U 内手牌的全部去重类键 -/
def keysOf (U : List Nat) (src : List Hand) : List (List Nat) :=
  dedupAux ((handSet U src).map classKey)

theorem keysOf_nodup (U : List Nat) (src : List Hand) : (keysOf U src).Nodup :=
  dedupAux_nodup _

theorem mem_keysOf {U : List Nat} {src : List Hand} {W : List Nat} :
    W ∈ keysOf U src ↔ ∃ H, H ∈ handSet U src ∧ classKey H = W := by
  rw [keysOf, mem_dedupAux, List.mem_map]

/-! ## 2. Nat 版码空间与预算引理 -/

def seqN (U : List Nat) : Nat → List (List Nat)
  | 0 => [[]]
  | k + 1 => U.flatMap (fun t => (seqN U k).map (fun c => t :: c))

theorem mem_seqN {U : List Nat} {k : Nat} {c : List Nat} :
    c ∈ seqN U k ↔ c.length = k ∧ ∀ x, x ∈ c → x ∈ U := by
  induction k generalizing c with
  | zero =>
    constructor
    · intro h
      have hc : c = [] := by simpa [seqN] using h
      subst hc; simp
    · rintro ⟨hlen, -⟩
      have hc : c = [] := List.eq_nil_of_length_eq_zero hlen
      subst hc; simp [seqN]
  | succ k ih =>
    rw [seqN, List.mem_flatMap]
    constructor
    · rintro ⟨a, haU, hc⟩
      rw [List.mem_map] at hc
      obtain ⟨c2, hc2, rfl⟩ := hc
      obtain ⟨hlen, hsub⟩ := ih.mp hc2
      refine ⟨by simp [hlen], ?_⟩
      intro x hx
      rcases List.mem_cons.mp hx with h | h
      · exact h.symm ▸ haU
      · exact hsub x h
    · rintro ⟨hlen, hsub⟩
      cases c with
      | nil => simp at hlen
      | cons a c2 =>
        refine ⟨a, hsub a List.mem_cons_self, ?_⟩
        rw [List.mem_map]
        refine ⟨c2, ih.mpr ⟨?_, ?_⟩, rfl⟩
        · simp at hlen; omega
        · intro x hx; exact hsub x (List.mem_cons_of_mem _ hx)

theorem seqN_length (U : List Nat) : ∀ k : Nat, (seqN U k).length = U.length ^ k
  | 0 => by simp [seqN]
  | k + 1 => by
    rw [seqN, List.length_flatMap]
    simp only [List.length_map]
    rw [List.map_const', sum_replicate, seqN_length U k, Nat.pow_succ]
    exact Nat.mul_comm _ _

theorem budgetNat {k : Nat} {U : List Nat} (cls : List (List (List Nat)))
    (hcls : cls.Nodup)
    (hlen : ∀ S, S ∈ cls → ∀ c, c ∈ S → c.length = k)
    (hsub : ∀ S, S ∈ cls → ∀ c, c ∈ S → ∀ x, x ∈ c → x ∈ U)
    (hdisj : ∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ c, c ∈ S → c ∈ T → False)
    (hSnodup : ∀ S, S ∈ cls → S.Nodup) :
    (cls.map List.length).sum ≤ U.length ^ k := by
  have hM : cls.flatten.Nodup := nodup_flatten_of_pairwise hcls hSnodup hdisj
  have hmem : ∀ c, c ∈ cls.flatten → c ∈ seqN U k := by
    intro c hc
    rw [List.mem_flatten] at hc
    obtain ⟨S, hS, hcS⟩ := hc
    exact mem_seqN.mpr ⟨hlen S hS c hcS, hsub S hS c hcS⟩
  have h := length_le_of_nodup_subset hM hmem
  rw [List.length_flatten, seqN_length] at h
  exact h

/-! ## 3. 通用引擎: 类数 > 码池 ⇒ 不可行 -/

def SC (P : Plan) (U : List Nat) (k : Nat) (W : List Nat) : List (List Nat) :=
  (P.codesOf W).filter (fun c => (c.length == k) && c.all (fun x => decide (x ∈ U)))

theorem SC_mem {P : Plan} {U : List Nat} {k : Nat} {W : List Nat} {c : List Nat} :
    c ∈ SC P U k W ↔ c ∈ P.codesOf W ∧ c.length = k ∧ ∀ x, x ∈ c → x ∈ U := by
  simp [SC, List.mem_filter, Bool.and_eq_true, beq_iff_eq, List.all_eq_true]

/-- **通用引擎**: 若 U 内听牌类数 N 超过码池 |U|^k, 则 k 不可行 -/
theorem noFeasible_of {U : List Nat} {src : List Hand} {k N : Nat}
    (hcount : (keysOf U src).length = N) (hbudget : U.length ^ k < N) :
    ¬ (∃ P : Plan, P.lengths k ∧ P.coversAll k ∧ P.disjoint ∧ P.valid) := by
  rintro ⟨P, hlenP, hcov, hdisjP, hvalid⟩
  let keys := keysOf U src
  let cls : List (List (List Nat)) := keys.map (fun W => dedupAux (SC P U k W))
  have hsub_code : ∀ W, W ∈ keys → SC P U k W ≠ [] := by
    intro W hW
    obtain ⟨H, hHT, hkey⟩ := mem_keysOf.mp hW
    obtain ⟨-, ⟨hinU, htot⟩, hw⟩ := mem_handSet.mp hHT
    obtain ⟨-, c, hc, hclen, hcont⟩ := hcov H htot hw
    have hcW : c ∈ P.codesOf W := by rw [← hkey]; exact hc
    have hsub : ∀ x, x ∈ c → x ∈ U := by
      intro x hx
      have hx34 : x < 34 := hvalid W c hcW x hx
      have hcnt : 0 < c.count x := List.count_pos_iff.mpr hx
      have hle : c.count x ≤ H.get ⟨x, hx34⟩ := by
        have h := hcont ⟨x, hx34⟩; simpa using h
      have hpos : 0 < H.get ⟨x, hx34⟩ := Nat.lt_of_lt_of_le hcnt hle
      exact inU_get hinU hpos
    intro hnil
    have : c ∈ SC P U k W := SC_mem.mpr ⟨hcW, hclen, hsub⟩
    rw [hnil] at this
    exact List.not_mem_nil this
  have hne : ∀ W, W ∈ keys → dedupAux (SC P U k W) ≠ [] := by
    intro W hW hnil
    exact hsub_code W hW (eq_nil_of_dedupAux_eq_nil hnil)
  -- 下界: 每类 ≥ 1
  have hlow : keys.length ≤ (cls.map List.length).sum := by
    have hmap : cls.map List.length = keys.map (fun W => (dedupAux (SC P U k W)).length) := by
      simp [cls]
    rw [hmap]
    refine length_le_sum_of_one_le (fun W hW => ?_)
    cases h : dedupAux (SC P U k W) with
    | nil => exact absurd h (hne W hW)
    | cons a t => simp only [List.length_cons]; omega
  have hcls_nodup : cls.Nodup := by
    have hinj : ∀ W, W ∈ keys → ∀ W', W' ∈ keys →
        dedupAux (SC P U k W) = dedupAux (SC P U k W') → W = W' := by
      intro W hW W' hW' heq
      by_cases hsame : W = W'
      · exact hsame
      · exfalso
        obtain ⟨c, hc⟩ := exists_mem_of_dedupAux_ne_nil (hne W hW)
        have hc1 : c ∈ P.codesOf W := (SC_mem.mp (mem_dedupAux.mp hc)).1
        have hc2 : c ∈ P.codesOf W' := by
          have hmem' : c ∈ dedupAux (SC P U k W') := by rw [← heq]; exact hc
          exact (SC_mem.mp (mem_dedupAux.mp hmem')).1
        exact hdisjP W W' hsame c hc1 hc2
    have := nodup_map hinj (keysOf_nodup U src)
    simpa [cls] using this
  have hSnodup : ∀ S, S ∈ cls → S.Nodup := by
    intro S hS
    rw [List.mem_map] at hS
    obtain ⟨W, -, rfl⟩ := hS
    exact dedupAux_nodup _
  have hlen' : ∀ S, S ∈ cls → ∀ c, c ∈ S → c.length = k := by
    intro S hS c hc
    rw [List.mem_map] at hS
    obtain ⟨W, -, rfl⟩ := hS
    exact (SC_mem.mp (mem_dedupAux.mp hc)).2.1
  have hsub' : ∀ S, S ∈ cls → ∀ c, c ∈ S → ∀ x, x ∈ c → x ∈ U := by
    intro S hS c hc x hx
    rw [List.mem_map] at hS
    obtain ⟨W, -, rfl⟩ := hS
    exact (SC_mem.mp (mem_dedupAux.mp hc)).2.2 x hx
  have hsetdisj : ∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ c, c ∈ S → c ∈ T → False := by
    intro S hS T hT hne3 c hc hcT
    obtain ⟨W, hW, hSW⟩ := List.mem_map.mp hS
    obtain ⟨W', hW', hTW⟩ := List.mem_map.mp hT
    have hWW' : W ≠ W' := by
      intro h; exact hne3 (by rw [← hSW, ← hTW, h])
    have hc1 : c ∈ P.codesOf W := (SC_mem.mp (mem_dedupAux.mp (by rw [hSW]; exact hc))).1
    have hc2 : c ∈ P.codesOf W' := (SC_mem.mp (mem_dedupAux.mp (by rw [hTW]; exact hcT))).1
    exact hdisjP W W' hWW' c hc1 hc2
  have hb := budgetNat (k := k) (U := U) cls hcls_nodup hlen' hsub' hsetdisj hSnodup
  have hcount' : keys.length = N := by simpa [keys] using hcount
  have hle : keys.length ≤ U.length ^ k := Nat.le_trans hlow hb
  rw [hcount'] at hle
  omega

/-! ## 4. 三条主定理 -/

/-- 前 9 张（单花色 U） -/
def u9N : List Nat := [0,1,2,3,4,5,6,7,8]

/-- U = {1..7}（k=3 否定用的 7 张子宇宙；与 Disproof.u7 同集合） -/
def u7N : List Nat := [1,2,3,4,5,6,7]

/-- 单花色 U 内听牌类数 = 387（native_decide，每条计数只算一次） -/
theorem keysFlush_count : (keysOf u9N flushHands).length = 387 := by native_decide

/-- U={1..7} 内听牌类数 = 347 -/
theorem keysU7_count : (keysOf u7N u7Hands).length = 347 := by native_decide

/-- **k=1 不可行**: 单花色 387 类 > 9^1 = 9 -/
theorem no_feasible_k1 : ¬ (∃ P : Plan, P.lengths 1 ∧ P.coversAll 1 ∧ P.disjoint ∧ P.valid) :=
  noFeasible_of (src := flushHands) (U := u9N) (k := 1) (N := 387) keysFlush_count (by decide)

/-- **k=2 不可行**: 单花色 387 类 > 9^2 = 81 -/
theorem no_feasible_k2 : ¬ (∃ P : Plan, P.lengths 2 ∧ P.coversAll 2 ∧ P.disjoint ∧ P.valid) :=
  noFeasible_of (src := flushHands) (U := u9N) (k := 2) (N := 387) keysFlush_count (by decide)

/-- **k=3 不可行**: U={1..7} 的 347 类 > 7^3 = 343 -/
theorem no_feasible_k3 : ¬ (∃ P : Plan, P.lengths 3 ∧ P.coversAll 3 ∧ P.disjoint ∧ P.valid) :=
  noFeasible_of (src := u7Hands) (U := u7N) (k := 3) (N := 347) keysU7_count (by decide)

#print axioms Mj.noFeasible_of
#print axioms Mj.no_feasible_k1
#print axioms Mj.no_feasible_k2
#print axioms Mj.no_feasible_k3

end Mj