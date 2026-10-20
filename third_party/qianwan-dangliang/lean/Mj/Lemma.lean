/-
  Mj.Lemma —— 「码空间 + 预算」引理层（Lean 4，仅 core/Std，无 mathlib）

  内容:
  * 码空间   seqU / codesU
  * 三条码空间引理  mem_codesU / codesU_nodup / codesU_length
  * 通用的「两两不交子表长度和 ≤ 母表长度」计数引理
  * 主定理 budget 及推论 classes_le_pow / no_common_code_two
-/
import Mj.Basic

namespace Mj

/-! ## 1. 码空间 -/

/-- U 的全部 k 元有序组 -/
def seqU (U : List Tile) : Nat → List (List Tile)
  | 0 => [[]]
  | k + 1 => U.flatMap (fun t => (seqU U k).map (fun c => t :: c))

/-- 码空间：U 的全部 k 元有序组 -/
def codesU (U : List Tile) (k : Nat) : List (List Tile) := seqU U k

@[simp] theorem seqU_zero (U : List Tile) : seqU U 0 = [[]] := rfl

@[simp] theorem seqU_succ (U : List Tile) (k : Nat) :
    seqU U (k + 1) = U.flatMap (fun t => (seqU U k).map (fun c => t :: c)) := rfl

@[simp] theorem codesU_eq (U : List Tile) (k : Nat) : codesU U k = seqU U k := rfl

/-- (1) c 是 U 的 k 元码 ⟺ c 长度为 k 且每个元素都在 U 里 -/
theorem mem_codesU {U : List Tile} {k : Nat} {c : List Tile} :
    c ∈ codesU U k ↔ c.length = k ∧ ∀ t, t ∈ c → t ∈ U := by
  induction k generalizing c with
  | zero =>
    constructor
    · intro h
      have hc : c = [] := by simpa using h
      subst hc
      simp
    · rintro ⟨hlen, -⟩
      have hc : c = [] := List.eq_nil_of_length_eq_zero hlen
      subst hc
      simp
  | succ k ih =>
    rw [codesU_eq, seqU_succ, List.mem_flatMap]
    constructor
    · rintro ⟨a, haU, hc⟩
      rw [List.mem_map] at hc
      obtain ⟨c', hc', rfl⟩ := hc
      obtain ⟨hlen, hsub⟩ := ih.mp hc'
      refine ⟨?_, ?_⟩
      · simp [hlen]
      · intro x hx
        rcases List.mem_cons.mp hx with h | h
        · exact h.symm ▸ haU
        · exact hsub x h
    · rintro ⟨hlen, hsub⟩
      cases c with
      | nil => simp only [List.length_nil] at hlen; omega
      | cons a c' =>
        refine ⟨a, hsub a List.mem_cons_self, ?_⟩
        rw [List.mem_map]
        refine ⟨c', ih.mpr ⟨?_, ?_⟩, rfl⟩
        · simp only [List.length_cons] at hlen; omega
        · intro x hx
          exact hsub x (List.mem_cons_of_mem _ hx)

/-! ## 2. 通用列表辅助引理 -/

/-- 把 List.map 的 Nodup 拆成「单射性 + 原表 Nodup」 -/
theorem nodup_map {α β : Type} {f : α → β} {l : List α}
    (hinj : ∀ a, a ∈ l → ∀ b, b ∈ l → f a = f b → a = b) (hl : l.Nodup) :
    (l.map f).Nodup := by
  induction l with
  | nil => simp
  | cons a t ih =>
    rw [List.nodup_cons] at hl
    obtain ⟨ha, ht⟩ := hl
    rw [List.map_cons, List.nodup_cons]
    refine ⟨?_, ?_⟩
    · intro hfa
      rw [List.mem_map] at hfa
      obtain ⟨b, hb, hfb⟩ := hfa
      have hab : a = b := hinj a List.mem_cons_self b (List.mem_cons_of_mem _ hb) hfb.symm
      exact ha (hab.symm ▸ hb)
    · exact ih (fun a ha b hb => hinj a (List.mem_cons_of_mem _ ha) b (List.mem_cons_of_mem _ hb)) ht

/-- flatMap 的 Nodup：每块 Nodup、不同块之间不交 -/
theorem nodup_flatMap {α β : Type} {l : List α} {f : α → List β}
    (hl : l.Nodup) (hf : ∀ a, a ∈ l → (f a).Nodup)
    (hd : ∀ a, a ∈ l → ∀ b, b ∈ l → a ≠ b → ∀ x, x ∈ f a → x ∈ f b → False) :
    (l.flatMap f).Nodup := by
  induction l with
  | nil => simp
  | cons a t ih =>
    rw [List.nodup_cons] at hl
    obtain ⟨ha, ht⟩ := hl
    rw [List.flatMap_cons, List.nodup_append]
    refine ⟨hf a List.mem_cons_self, ?_, ?_⟩
    · exact ih ht (fun b hb => hf b (List.mem_cons_of_mem _ hb))
        (fun b hb c hc hne => hd b (List.mem_cons_of_mem _ hb) c (List.mem_cons_of_mem _ hc) hne)
    · intro x hx y hy hxy
      rw [List.mem_flatMap] at hy
      obtain ⟨b, hb, hyb⟩ := hy
      exact hd a List.mem_cons_self b (List.mem_cons_of_mem _ hb)
        (fun h => ha (h.symm ▸ hb)) x hx (hxy.symm ▸ hyb)

/-- (List.replicate n a).sum = n * a -/
theorem sum_replicate (a : Nat) : ∀ n : Nat, (List.replicate n a).sum = n * a
  | 0 => by simp
  | n + 1 => by
    rw [List.replicate_succ, List.sum_cons, sum_replicate a n, Nat.succ_mul]
    exact Nat.add_comm a (n * a)

/-- 若每项都 ≥ 1，则表长 ≤ 各项之和 -/
theorem length_le_sum_of_one_le {α : Type} {l : List α} {f : α → Nat}
    (h : ∀ x, x ∈ l → 1 ≤ f x) : l.length ≤ (l.map f).sum := by
  induction l with
  | nil => simp
  | cons a t ih =>
    simp only [List.length_cons, List.map_cons, List.sum_cons]
    have h1 := h a List.mem_cons_self
    have h2 := ih (fun x hx => h x (List.mem_cons_of_mem _ hx))
    omega

/-- L.Nodup 时，逐元素落在 L 里的 Nodup 表 M 满足 |M| ≤ |L| -/
theorem length_le_of_nodup_subset {α : Type} [DecidableEq α] {M L : List α}
    (hM : M.Nodup) (hsub : ∀ x, x ∈ M → x ∈ L) : M.length ≤ L.length := by
  induction L generalizing M with
  | nil =>
    have hMnil : M = [] :=
      List.eq_nil_iff_forall_not_mem.mpr (fun x hx => List.not_mem_nil (hsub x hx))
    subst hMnil
    simp
  | cons a L ih =>
    by_cases hmem : a ∈ M
    · have hsub' : ∀ x, x ∈ M.erase a → x ∈ L := by
        intro x hx
        have hxM : x ∈ M := List.erase_sublist.subset hx
        have hne : x ≠ a := fun h => List.Nodup.not_mem_erase hM (h ▸ hx)
        rcases List.mem_cons.mp (hsub x hxM) with h | h
        · exact absurd h hne
        · exact h
      have hErase : (M.erase a).Nodup := hM.erase a
      have ih' := ih hErase hsub'
      have hlen : (M.erase a).length = M.length - 1 := List.length_erase_of_mem hmem
      have hpos : 1 ≤ M.length := List.length_pos_iff_exists_mem.mpr ⟨a, hmem⟩
      simp only [List.length_cons]
      omega
    · have hsub' : ∀ x, x ∈ M → x ∈ L := by
        intro x hx
        rcases List.mem_cons.mp (hsub x hx) with h | h
        · exact absurd (h ▸ hx) hmem
        · exact h
      have ih' := ih hM hsub'
      simp only [List.length_cons]
      omega

/-- 两两不交、类内 Nodup 的类族的拼接仍是 Nodup -/
theorem nodup_flatten_of_pairwise {α : Type} {cls : List (List α)}
    (hcls : cls.Nodup) (hnodup : ∀ S, S ∈ cls → S.Nodup)
    (hdisj : ∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ x, x ∈ S → x ∈ T → False) :
    cls.flatten.Nodup := by
  induction cls with
  | nil => simp
  | cons S cls ih =>
    rw [List.nodup_cons] at hcls
    obtain ⟨hSnotin, hcls'⟩ := hcls
    rw [List.flatten_cons, List.nodup_append]
    refine ⟨hnodup S List.mem_cons_self, ?_, ?_⟩
    · exact ih hcls' (fun T hT => hnodup T (List.mem_cons_of_mem _ hT))
        (fun T hT T' hT' hne =>
          hdisj T (List.mem_cons_of_mem _ hT) T' (List.mem_cons_of_mem _ hT') hne)
    · intro x hx y hy
      rw [List.mem_flatten] at hy
      obtain ⟨T, hT, hyT⟩ := hy
      exact fun hxy => hdisj S List.mem_cons_self T (List.mem_cons_of_mem _ hT)
        (fun h => hSnotin (h ▸ hT)) x hx (hxy.symm ▸ hyT)

/-! ## 3. 码空间引理 -/

/-- (2) U.Nodup 时码空间无重复 -/
theorem codesU_nodup {U : List Tile} (hU : U.Nodup) : ∀ k, (codesU U k).Nodup
  | 0 => by rw [codesU_eq, seqU_zero]; simp
  | k + 1 => by
    rw [codesU_eq, seqU_succ]
    refine nodup_flatMap hU (fun t _ => ?_) (fun t _ t' _ hne x hx hy => ?_)
    · refine nodup_map (fun c _ c' _ h => ?_) (codesU_nodup hU k)
      exact (List.cons.inj h).2
    · rw [List.mem_map] at hx hy
      obtain ⟨c, -, rfl⟩ := hx
      obtain ⟨c', -, hc'⟩ := hy
      exact hne (List.cons.inj hc').1.symm

/-- (3) 码空间的大小 = |U|^k -/
theorem seqU_length (U : List Tile) : ∀ k, (seqU U k).length = U.length ^ k
  | 0 => by rw [seqU_zero]; simp
  | k + 1 => by
    rw [seqU_succ, List.length_flatMap]
    simp only [List.length_map]
    rw [List.map_const', sum_replicate, seqU_length U k, Nat.pow_succ]
    exact Nat.mul_comm _ _

theorem codesU_length (U : List Tile) (k : Nat) : (codesU U k).length = U.length ^ k :=
  seqU_length U k

/-! ## 4. 主定理与推论 -/

/-- 预算定理：U.Nodup + 类两两不同 + 类内码不重复 + 类两两不交
    ⟹ 各类码数之和 ≤ |U|^k -/
theorem budget {k : Nat} {U : List Tile} (hU : U.Nodup) (cls : List (List (List Tile)))
    (hcls : cls.Nodup)
    (hlen : ∀ S, S ∈ cls → ∀ c, c ∈ S → c.length = k)
    (hsub : ∀ S, S ∈ cls → ∀ c, c ∈ S → ∀ t, t ∈ c → t ∈ U)
    (hdisj : ∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ c, c ∈ S → c ∈ T → False)
    (hSnodup : ∀ S, S ∈ cls → S.Nodup) :
    (cls.map List.length).sum ≤ U.length ^ k := by
  -- 环境码空间是无重复表（hU 在码空间引理里的作用）
  have hL : (codesU U k).Nodup := codesU_nodup hU k
  have hM : cls.flatten.Nodup := nodup_flatten_of_pairwise hcls hSnodup hdisj
  have hmem : ∀ c, c ∈ cls.flatten → c ∈ codesU U k := by
    intro c hc
    rw [List.mem_flatten] at hc
    obtain ⟨S, hS, hcS⟩ := hc
    exact mem_codesU.mpr ⟨hlen S hS c hcS, hsub S hS c hcS⟩
  have h := length_le_of_nodup_subset hM hmem
  rw [List.length_flatten, codesU_length] at h
  exact h

/-- 推论 ①：每类非空 ⟹ 类数 ≤ |U|^k -/
theorem classes_le_pow {k : Nat} {U : List Tile} (hU : U.Nodup) (cls : List (List (List Tile)))
    (hcls : cls.Nodup)
    (hlen : ∀ S, S ∈ cls → ∀ c, c ∈ S → c.length = k)
    (hsub : ∀ S, S ∈ cls → ∀ c, c ∈ S → ∀ t, t ∈ c → t ∈ U)
    (hdisj : ∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ c, c ∈ S → c ∈ T → False)
    (hSnodup : ∀ S, S ∈ cls → S.Nodup)
    (hne : ∀ S, S ∈ cls → S ≠ []) : cls.length ≤ U.length ^ k := by
  have hb := budget hU cls hcls hlen hsub hdisj hSnodup
  have h1 : cls.length ≤ (cls.map List.length).sum := by
    refine length_le_sum_of_one_le (fun S hS => ?_)
    cases S with
    | nil => exact absurd rfl (hne [] hS)
    | cons a t => simp only [List.length_cons]; omega
  exact Nat.le_trans h1 hb

/-- 推论 ②：若命中集 S 的每个元素都是 U 上的 k-码，且没有这样的码被所有 H 包含，
    则 |S| ≥ 2。

    注意：题面给出的原始语句缺少「S 的元素都是 U 上的 k-码」这一条 hS，
    而该假设是 hno 唯一可用的入口，缺了它命题为假。 -/
theorem no_common_code_two {k : Nat} {U : List Tile} {Hs : List (List (List Tile))}
    (hHsne : Hs ≠ []) (S : List (List Tile))
    (hS : ∀ c, c ∈ S → c.length = k ∧ ∀ t, t ∈ c → t ∈ U)
    (hcover : ∀ H, H ∈ Hs → ∃ c, c ∈ S ∧ c ∈ H)
    (hno : ∀ c, c.length = k → (∀ t, t ∈ c → t ∈ U) → ∃ H, H ∈ Hs ∧ c ∉ H) :
    2 ≤ S.length := by
  obtain ⟨H0, hH0⟩ := List.exists_mem_of_ne_nil Hs hHsne
  cases S with
  | nil =>
    obtain ⟨c, hc, -⟩ := hcover H0 hH0
    simp at hc
  | cons c S' =>
    cases S' with
    | nil =>
      obtain ⟨hlen, hsubc⟩ := hS c List.mem_cons_self
      obtain ⟨H, hH, hnc⟩ := hno c hlen hsubc
      obtain ⟨c', hc'S, hc'H⟩ := hcover H hH
      rw [List.mem_singleton] at hc'S
      exact absurd (hc'S ▸ hc'H) hnc
    | cons c2 S'' =>
      simp only [List.length_cons]
      omega

/-! ## 5. 与 Basic.contains（Bool 版）的桥接 -/

/-- contains 的 Bool 判据 ⟺ Prop 版逐牌计数比较（Lead 建议的 Bool/Prop 桥） -/
theorem contains_eq_true_iff (code : List Tile) (H : Hand) :
    contains code H = true ↔ ∀ t : Tile, code.count t ≤ H.get t := by
  rw [contains, List.all_eq_true]
  constructor
  · intro h t
    simpa using h t (List.mem_finRange t)
  · intro h t _
    simpa using h t

end Mj

#print axioms Mj.budget
#print axioms Mj.classes_le_pow
#print axioms Mj.no_common_code_two
#print axioms Mj.contains_eq_true_iff
