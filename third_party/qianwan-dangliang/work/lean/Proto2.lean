import Mj.Basic

namespace Mj

def catLen (c : Nat) : Nat := if c < 3 then 9 else 7
def catBase (c : Nat) : Nat := if c < 3 then c * 9 else 27

/-- 第一个非零位置 -/
def firstNz : List Nat → Nat → Option Nat
  | [], _ => none
  | x :: xs, i => if x > 0 then some i else firstNz xs (i + 1)

/-- 计数向量 v 能否拆成若干面子（honors=true 时只允许刻子） -/
def canMelds : Bool → Nat → List Nat → Bool
  | honors, 0, v => v.all (fun x => x == 0)
  | honors, fuel + 1, v =>
    match firstNz v 0 with
    | none => true
    | some i =>
      let c := v.getD i 0
      (decide (c ≥ 3) && canMelds honors fuel (v.set i (c - 3))) ||
      (if honors then false
       else if i + 2 < v.length && v.getD (i + 1) 0 > 0 && v.getD (i + 2) 0 > 0 then
         canMelds honors fuel
           (((v.set i (c - 1)).set (i + 1) (v.getD (i + 1) 0 - 1)).set (i + 2) (v.getD (i + 2) 0 - 1))
       else false)

def meldsOk (c : Nat) (v : List Nat) : Bool := canMelds (c == 3) (v.foldl (fun a x => a + x) 0) v

/-- ∃ 雀头 p：v - 2e_p 可拆成面子 -/
def pdVec (c : Nat) (v : List Nat) : Bool :=
  (List.range v.length).any (fun p => decide (v.getD p 0 ≥ 2) && meldsOk c (v.set p (v.getD p 0 - 2)))

/-- Wp（全局掩码）：X+t 可拆成面子+雀头 -/
def wpOf (c : Nat) (X : List Nat) : Nat :=
  (List.range X.length).foldl (fun acc t =>
    if X.getD t 0 < 4 && pdVec c (X.set t (X.getD t 0 + 1)) then acc ||| (1 <<< (catBase c + t)) else acc) 0

/-- V（全局掩码）：X+t 全为面子 -/
def vOf (c : Nat) (X : List Nat) : Nat :=
  (List.range X.length).foldl (fun acc t =>
    if X.getD t 0 < 4 && meldsOk c (X.set t (X.getD t 0 + 1)) then acc ||| (1 <<< (catBase c + t)) else acc) 0

def oddCount (X : List Nat) : Nat := X.foldl (fun a x => a + x % 2) 0

def otOf (c : Nat) (X : List Nat) : Option Nat :=
  let idxs := (List.range X.length).filter (fun i => X.getD i 0 % 2 == 1)
  if idxs.length == 1 then some (catBase c + idxs.headD 0) else none

/-- flags_vec: a2 = 所有非零项都等于 2 -/
def a2Of (X : List Nat) : Bool := X.all (fun x => x == 0 || x == 2)

/-- o2 = 恰有一个 1 且其余非零项都等于 2 -/
def o2Of (X : List Nat) : Bool :=
  X.all (fun x => x == 0 || x == 1 || x == 2) && (X.filter (fun x => x == 1)).length == 1

structure ProfKey where
  V : Nat
  pd : Bool
  odd : Nat
  ot : Option Nat
  a2 : Bool
  o2 : Bool
deriving BEq, DecidableEq, Repr

/-- II 型 profile 键 k = (V, pd, odd, ot, a2, o2) -/
def iiKey (c : Nat) (X : List Nat) : ProfKey :=
  { V := vOf c X, pd := pdVec c X, odd := oddCount X, ot := otOf c X, a2 := a2Of X, o2 := o2Of X }

/-- 计数向量的 order-independent 校验和（base 5） -/
def encX (X : List Nat) : Nat :=
  (List.range X.length).foldl (fun acc i => acc + X.getD i 0 * 5 ^ i) 0

/-- profile 键编码成一个 Nat（用于排序/聚合） -/
def keyEnc (k : ProfKey) : Nat :=
  k.V + (if k.pd then 1 else 0) * 2 ^ 34 + k.odd * 2 ^ 35 +
  (match k.ot with | none => 34 | some t => t) * 2 ^ 39 +
  (if k.a2 then 1 else 0) * 2 ^ 45 + (if k.o2 then 1 else 0) * 2 ^ 46

/-- 枚举：长度 len、总和 size、每项 <= 4 的全部计数向量 -/
def enumGo : Nat → Nat → List Nat → List (List Nat)
  | 0, rem, acc => if rem == 0 then [acc.reverse] else []
  | fuel + 1, rem, acc =>
    (List.range (min 4 rem + 1)).flatMap (fun k => enumGo fuel (rem - k) (k :: acc))

def enumX (len size : Nat) : List (List Nat) := enumGo len size []

/-- 聚合：[(keyEnc, |xs|, Σenc)]，按 keyEnc 排序 -/
def ins3 (x : Nat × Nat × Nat) : List (Nat × Nat × Nat) → List (Nat × Nat × Nat)
  | [] => [x]
  | y :: ys => if decide (x.1 ≤ y.1) then x :: y :: ys else y :: ins3 x ys

def isort3 (xs : List (Nat × Nat × Nat)) : List (Nat × Nat × Nat) :=
  xs.foldl (fun acc x => ins3 x acc) []

def aggOf (c s : Nat) : List (Nat × Nat × Nat) :=
  let m : Std.HashMap Nat (Nat × Nat) :=
    (enumX (catLen c) s).foldl (fun m X =>
      let ke := keyEnc (iiKey c X)
      match m.get? ke with
      | some e => m.insert ke (e.1 + 1, e.2 + encX X)
      | none => m.insert ke (1, encX X)) {}
  isort3 (m.toList.map (fun (ke, e) => (ke, e.1, e.2)))

end Mj

open Mj
#eval (enumX 9 2).length
#eval (enumX 9 11).length
#eval (enumX 7 11).length
#eval (aggOf 0 2).length
#eval (aggOf 0 11).length
#eval (aggOf 3 2)
#eval (aggOf 0 5)
