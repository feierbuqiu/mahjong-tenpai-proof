import Mj.Basic

open Mj

namespace Cex

def t0 : Tile := ⟨0, by decide⟩
def U : List Tile := [t0]
def cls : List (List (List Tile)) := [[[t0], [t0]]]

example : U.Nodup = true := by decide
example : (cls.all (fun S => S.all (fun c => c.length = 1 ∧ c.all (fun t => t ∈ U)))) = true := by decide
example : ¬ ((cls.map List.length).sum ≤ U.length ^ 1) := by decide
example : (cls.map List.length).sum = 2 := by decide
def cls2 : List (List (List Tile)) := [[[t0]], [[t0]]]
example : ¬ ((cls2.map List.length).sum ≤ U.length ^ 1) := by decide

/-! ### 推论② 原语句（缺 hS）为假: k=0, U=[t0], Hs=[[[t0]]], S=[[t0]] -/
example : ([[[t0]]] : List (List (List Tile))) ≠ [] := by decide
example : (∀ H, H ∈ ([[[t0]]] : List (List (List Tile))) →
    ∃ c, c ∈ ([[t0]] : List (List Tile)) ∧ c ∈ H) := by
  intro H hH
  simp only [List.mem_singleton] at hH
  subst hH
  exact ⟨[t0], by simp, by simp⟩
example : (∀ c : List Tile, c.length = 0 → (∀ t, t ∈ c → t ∈ U) →
    ∃ H, H ∈ ([[[t0]]] : List (List (List Tile))) ∧ c ∉ H) := by
  intro c hlen _
  have hc : c = [] := List.eq_nil_of_length_eq_zero hlen
  subst hc
  exact ⟨[[t0]], by simp, by simp⟩
example : ¬ (2 ≤ ([[t0]] : List (List Tile)).length) := by decide

end Cex
