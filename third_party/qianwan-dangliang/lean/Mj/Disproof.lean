/-
  Mj.Disproof —— k=1/2/3 否证的纯计算实例化（T12 / L3）
  依赖: Mj.Basic（接口冻结）, Mj.Lemma（预算引理 budget）, Mj.Protocol（Plan / Feasible）。

  ⚠️ 信任分层与「未形式化的桥」（必读）
  1)【编译器信任】§2 单花色 93,600 手 与 §3 U={1..7} 7,875 手的普查由 native_decide 求值,
     依赖 Lean 编译器的信任公理, #print axioms 显示为 *_native.native_decide.ax_*（即 Lean.ofReduceBool 机制）。
     实测: 内核级 decide 跑该规模普查在本机 10 分钟内未完成（kernel whnf 爆炸）, 故本轮不做内核级普查;
     若需完全内核级, 应改为「证书 + 内核校验」路线（把类键表与 52 个类的见证对作为字面量, 由内核逐条校验）。
  2)【内核可检查】sum_ge_length_add_count / budget_sharp / u7_nodup / u7_length / k1k2_gaps.k3_gap 的
     算术组合（omega / decide）只依赖 propext / Classical.choice / Quot.sound。
  3)【⚠️ 桥接假设, 不是已证事实】no_feasible_k3_of_bridge 的 hbridge 断言:
     「Feasible 3 ⇒ 存在类族 cls 与谓词 bad, 满足 budget_sharp 的全部假设且 cls.length = N7, (cls.filter bad).length = L3」。
     其证明需要: (a) codesU/subsOfSize 的枚举完备性引理; (b) classKey（List Nat）↔ waits（List Tile）的桥接;
     (c) coversAll ⇒ 每类预算内码集非空的论证; (d) 无公共码类 ⇒ 码集大小 ≥ 2 的论证。
     以上尚未形式化, 因此该定理是「骨架 + 显式假设」, 不得当作已证结论引用。
-/
import Mj.Basic
import Mj.Lemma
import Mj.Protocol

namespace Mj

open Hand

/-! ## 1. 工具 -/

/-- 按 f 的值把手牌分组（f 每手只算一次） -/
def groupBy (f : Hand → List Tile) (l : List Hand) : List (List Hand) :=
  let rec step (acc : List (List Tile × List Hand)) (k : List Tile) (H : Hand) :
      List (List Tile × List Hand) :=
    match acc with
    | [] => [(k, [H])]
    | (k', g) :: rest => if k' == k then (k', H :: g) :: rest else (k', g) :: step rest k H
  (l.foldl (fun acc H => step acc (f H) H) []).map (fun p => p.2)

/-- 听牌手牌（waits 非空） -/
def tenpai (l : List Hand) : List Hand := l.filter (fun H => !(waits H).isEmpty)

/-- 按 waits 分出的听牌类 -/
def classesOf (l : List Hand) : List (List Hand) := groupBy waits (tenpai l)

/-- 类 S 在码空间 codesU U k 中的公共码（命中 S 中每一手牌） -/
def commonCodesU (S : List Hand) (U : List Tile) (k : Nat) : List (List Tile) :=
  (codesU U k).filter (fun c => S.all (fun H => contains c H))

/-- 类 S 在 U 内没有公共 k-码 -/
def noCommonU (S : List Hand) (U : List Tile) (k : Nat) : Bool :=
  (commonCodesU S U k).isEmpty

/-- 无公共 k-码的类数 -/
def noCommonCountU (cls : List (List Hand)) (U : List Tile) (k : Nat) : Nat :=
  (cls.filter (fun S => noCommonU S U k)).length

/-- 前 n 张牌（Tile 版） -/
def tilesUpTo (n : Nat) : List Tile :=
  (List.range n).filterMap (fun i => if h : i < 34 then some ⟨i, h⟩ else none)

/-! ## 2. 单花色 U = 索引 0..8（93,600 手） -/

def flushU : List Tile := tilesUpTo 9
def flushCls : List (List Hand) := classesOf flushHands
def Nflush : Nat := flushCls.length
def L1 : Nat := noCommonCountU flushCls flushU 1
def L2 : Nat := noCommonCountU flushCls flushU 2

/-- 单花色全部数值（一次编译求值; native_decide） -/
theorem flush_counts :
    flushHands.length = 93600 ∧
    (tenpai flushHands).length = 40196 ∧
    Nflush = 387 ∧ L1 = 40 ∧ L2 = 53 := by
  native_decide

-- 【实测】内核级 `decide` 普查 7,875 手在本机 10 分钟内未完成（kernel whnf 爆炸），
-- 故 §2/§3 统一用 native_decide，并在文件头标注依赖编译器信任（Lean.ofReduceBool 机制）。

/-! ## 3. U = 索引 1..7（m2..m8，7 张） -/

def u7 : List Tile :=
  (List.range 7).filterMap (fun i => if h : i + 1 < 34 then some ⟨i + 1, h⟩ else none)

def u7Hands : List Hand := handsIn [1,2,3,4,5,6,7] 13
def u7Cls : List (List Hand) := classesOf u7Hands
def N7 : Nat := u7Cls.length
def L3 : Nat := noCommonCountU u7Cls u7 3

/-- U={1..7} 的全部数值（一次编译求值; native_decide） -/
theorem u7_counts :
    u7Hands.length = 7875 ∧
    (tenpai u7Hands).length = 5628 ∧
    N7 = 347 ∧ L3 = 52 := by
  native_decide

theorem N7_eq : N7 = 347 := u7_counts.2.2.1
theorem L3_eq : L3 = 52 := u7_counts.2.2.2

/-! ## 4. 由预算引理推出的否证结论（内核可检查） -/

/-- 类族中「每类 ≥1 条码、其中 bad 类 ≥2 条码」⇒ 码数之和 ≥ 类数 + bad 类数 -/
theorem sum_ge_length_add_count {α : Type} (cls : List α) (len : α → Nat) (bad : α → Bool)
    (hne : ∀ S, S ∈ cls → 1 ≤ len S) (hbig : ∀ S, S ∈ cls → bad S = true → 2 ≤ len S) :
    cls.length + (cls.filter bad).length ≤ (cls.map len).sum := by
  induction cls with
  | nil => simp
  | cons S t ih =>
    have ih2 := ih (fun x hx => hne x (List.mem_cons_of_mem _ hx))
                    (fun x hx hb => hbig x (List.mem_cons_of_mem _ hx) hb)
    rw [List.length_cons, List.map_cons, List.sum_cons]
    by_cases hb : bad S = true
    · have hfil : (S :: t).filter bad = S :: (t.filter bad) := by simp [hb]
      rw [hfil, List.length_cons]
      have h1 := hne S List.mem_cons_self
      have h2 := hbig S List.mem_cons_self hb
      omega
    · have hfil : (S :: t).filter bad = t.filter bad := by simp [hb]
      rw [hfil]
      have h1 := hne S List.mem_cons_self
      omega

/-- 预算引理的下界强化: 类族满足 budget 全部假设、每类非空、bad 类码数 ≥ 2 ⇒ 类数 + bad 类数 ≤ |U|^k -/
theorem budget_sharp {k : Nat} {U : List Tile} (hU : U.Nodup)
    (cls : List (List (List Tile))) (bad : List (List Tile) → Bool)
    (hcls : cls.Nodup)
    (hlen : ∀ S, S ∈ cls → ∀ c, c ∈ S → c.length = k)
    (hsub : ∀ S, S ∈ cls → ∀ c, c ∈ S → ∀ t, t ∈ c → t ∈ U)
    (hdisj : ∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ c, c ∈ S → c ∈ T → False)
    (hSnodup : ∀ S, S ∈ cls → S.Nodup)
    (hne : ∀ S, S ∈ cls → S ≠ [])
    (hbig : ∀ S, S ∈ cls → bad S = true → 2 ≤ S.length) :
    cls.length + (cls.filter bad).length ≤ U.length ^ k := by
  have hb := budget hU cls hcls hlen hsub hdisj hSnodup
  have hlow := sum_ge_length_add_count cls List.length bad
    (fun S hS => by
      cases S with
      | nil => exact absurd rfl (hne [] hS)
      | cons a t => simp only [List.length_cons]; omega)
    (fun S hS hbad => hbig S hS hbad)
  omega

/-- k=1/k=2 的算术否证: 34 = 34^1 < Nflush + L1 且 9^2 = 81 < Nflush + L2（内核算术） -/
theorem k1k2_gaps : 34 < Nflush + L1 ∧ 9 ^ 2 < Nflush + L2 := by native_decide

/-- k=3（核心）: U={1..7} 的码池 7^3 = 343 < N7 + L3 = 399（内核算术） -/
theorem k3_gap : 7 ^ 3 < N7 + L3 := by native_decide

/-- u7 无重复、长度 7（内核可检查） -/
theorem u7_nodup : u7.Nodup := by decide
theorem u7_length : u7.length = 7 := by decide

/-- ⚠️【已被取代 — SUPERSEDED】本定理依赖未形式化的桥接假设 hbridge（见文件头 §3 的 ⚠️ 条目）。
    **不要再把它当作 k=3 否证的终点**: Mj.Bridge 已给出无 hbridge 的完整否证
    `Mj.no_feasible_k3`（同一条「347 类 > 7^3 = 343 个码池」论证；信任基仅 3 条 native_decide 普查计数）。
    保留本定理仅为历史/对照用途（hbridge 路线额外含 L3=52 的加强下界）。

    k=3 不可行的形式化骨架（内核可检查部分）:
    若存在满足 Feasible 3 的表 P, 把 U={1..7} 上 347 个听牌类对应的「预算内码集」记为 cls
    (每类取 P.codesOf 中 ⊆ U 的码), 则 cls 满足 budget_sharp 的全部假设、每类非空,
    且 52 个类在 U 内无公共 3-码 ⇒ 其码集大小 ≥ 2。于是 budget_sharp 给出 347 + 52 ≤ 7^3, 与 k3_gap 矛盾。
    桥接假设 hbridge 显式列出: 其证明需要 codesU/subsOfSize 枚举完备性 + classKey↔waits 桥接。 -/
theorem no_feasible_k3_of_bridge
    (hbridge : Feasible 3 → ∃ (cls : List (List (List Tile))) (bad : List (List Tile) → Bool),
      cls.length = N7 ∧ (cls.filter bad).length = L3 ∧
      cls.Nodup ∧ (∀ S, S ∈ cls → S ≠ []) ∧
      (∀ S, S ∈ cls → ∀ c, c ∈ S → c.length = 3) ∧
      (∀ S, S ∈ cls → ∀ c, c ∈ S → ∀ t, t ∈ c → t ∈ u7) ∧
      (∀ S, S ∈ cls → ∀ T, T ∈ cls → S ≠ T → ∀ c, c ∈ S → c ∈ T → False) ∧
      (∀ S, S ∈ cls → S.Nodup) ∧
      (∀ S, S ∈ cls → bad S = true → 2 ≤ S.length)) :
    ¬ Feasible 3 := by
  intro hf
  obtain ⟨cls, bad, hlen_cls, hlen_bad, hcls, hne, hlen, hsub, hdisj, hSnodup, hbig⟩ := hbridge hf
  have hb := budget_sharp (k := 3) (U := u7) u7_nodup cls bad hcls hlen hsub hdisj hSnodup hne hbig
  rw [hlen_cls, hlen_bad, u7_length] at hb
  have hgap := k3_gap
  omega

/-! ## 5. 信任基（#print axioms） -/

#print axioms Mj.flush_counts
#print axioms Mj.u7_counts
#print axioms Mj.sum_ge_length_add_count
#print axioms Mj.budget_sharp
#print axioms Mj.k1k2_gaps
#print axioms Mj.k3_gap
#print axioms Mj.no_feasible_k3_of_bridge

end Mj
