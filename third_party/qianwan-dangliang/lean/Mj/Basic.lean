/-
  Mj.Basic —— 麻将「翻牌猜听牌」问题的形式化基础层（Lean 4，只用 core/Std，不依赖 mathlib）
  牌：34 种；手牌：长度 34 的计数数组（每种 ≤ 4 张，由构造保证）。
  规则：天凤（日本麻将）—— 七对子须为 7 种不同牌各 2 张；字牌（索引 27..33）不能组顺子。
-/
import Std

namespace Mj

abbrev Tile := Fin 34

/-- 手牌（计数向量；约定 size = 34 且每项 ≤ 4） -/
structure Hand where
  v : Array Nat
deriving Repr, BEq, DecidableEq

namespace Hand

def get (H : Hand) (t : Tile) : Nat := H.v.getD t.val 0

def set (H : Hand) (t : Tile) (n : Nat) : Hand := ⟨H.v.set! t.val n⟩

def total (H : Hand) : Nat := H.v.foldl (fun a b => a + b) 0

end Hand

def Hand.add? (H : Hand) (t : Tile) : Option Hand :=
  if H.get t < 4 then some (H.set t (H.get t + 1)) else none

/-! ## 和牌判定（纯计算） -/

def kokushiIdx : List Nat := [0, 8, 9, 17, 18, 26, 27, 28, 29, 30, 31, 32, 33]

def vecTotal (v : Array Nat) : Nat := v.foldl (fun a b => a + b) 0

def firstNonzero (v : Array Nat) : Option Nat := (List.range 34).find? (fun i => v.getD i 0 > 0)

/-- 把所有牌拆成面子（3 张的刻子或顺子） -/
def allMelds : Nat → Array Nat → Bool
  | 0, v => (firstNonzero v).isNone
  | fuel + 1, v =>
    match firstNonzero v with
    | none => true
    | some i =>
      let c := v.getD i 0
      (if c ≥ 3 then allMelds fuel (v.set! i (c - 3)) else false) ||
      (if i < 27 ∧ i % 9 ≤ 6 ∧ v.getD (i+1) 0 > 0 ∧ v.getD (i+2) 0 > 0 then
         allMelds fuel
           (((v.set! i (c - 1)).set! (i+1) (v.getD (i+1) 0 - 1)).set! (i+2) (v.getD (i+2) 0 - 1))
       else false)

/-- 标准型：4 面子 + 1 雀头 -/
def stdWin (v : Array Nat) : Bool :=
  vecTotal v == 14 &&
  (List.range 34).any (fun i =>
    if v.getD i 0 ≥ 2 then allMelds 4 (v.set! i (v.getD i 0 - 2)) else false)

/-- 严格七对子：恰 7 种牌各 2 张（4 张同牌不算两对） -/
def chiitoiWin (v : Array Nat) : Bool :=
  vecTotal v == 14 && ((List.range 34).filter (fun i => v.getD i 0 == 2)).length == 7

/-- 国士无双：恰由 13 种幺九构成（各 ≥1 张），共 14 张，且**不含任何非幺九牌** -/
def kokushiWin (v : Array Nat) : Bool :=
  vecTotal v == 14 &&
  (List.range 34).all (fun i => if v.getD i 0 > 0 then kokushiIdx.contains i else true) &&
  kokushiIdx.all (fun i => v.getD i 0 ≥ 1)

def isWinVec (v : Array Nat) : Bool :=
  vecTotal v == 14 && (stdWin v || chiitoiWin v || kokushiWin v)

def isWin (H : Hand) : Bool := isWinVec H.v

/-- 听牌集合（13 张手牌）：所有 t 使 H.t < 4 且 H+t 和牌 -/
def waits (H : Hand) : List Tile :=
  if H.total = 13 then
    (List.finRange 34).filter (fun t => H.get t < 4 && isWinVec (H.v.set! t.val (H.get t + 1)))
  else []

/-- 码（有序元组）的多重集 ⊆ 手牌 -/
def contains (code : List Tile) (H : Hand) : Bool :=
  (List.finRange 34).all (fun t => code.count t ≤ H.get t)

/-! ## 枚举 -/

/-- 枚举 support ⊆ tiles（牌索引）、总数 = tot、每张 ≤ 4 的全部手牌 -/
def handsIn (tiles : List Nat) (tot : Nat) : List Hand :=
  let rec go : List Nat → Nat → Array Nat → List Hand
    | [], rem, v => if rem = 0 then [⟨v⟩] else []
    | t :: ts, rem, v => (List.range (min 4 rem + 1)).flatMap (fun k => go ts (rem - k) (v.set! t k))
  go tiles tot (List.replicate 34 0).toArray

/-- 单花色 13 张手牌全枚举（93,600 个） -/
def flushHands : List Hand := handsIn (List.range 9) 13

/-- 手牌的全部 k-子多重集（码候选） -/
def subsOfSize (H : Hand) (k : Nat) : List (List Nat) :=
  let rec go (t : Nat) (rem : Nat) : List (List Nat) :=
    if h : t < 34 then
      (List.range (min (H.get ⟨t, h⟩) rem + 1)).flatMap (fun c =>
        (go (t+1) (rem - c)).map (fun rest => List.replicate c t ++ rest))
    else if rem = 0 then [[]] else []
  termination_by 34 - t
  decreasing_by omega
  go 0 k

end Mj
