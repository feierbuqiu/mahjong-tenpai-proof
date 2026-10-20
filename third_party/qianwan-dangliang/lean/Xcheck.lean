import Mj.Basic
open Mj

def parseHand (s : String) : Hand :=
  let parts := s.splitOn ","
  let arr : Array Nat := parts.foldl (fun a p => a.push (p.toNat!)) #[]
  ⟨arr⟩

def main : IO Unit := do
  let content ← IO.FS.readFile "../work/lean_hand_input.txt"
  let mut out := ""
  for line in content.splitOn "\n" do
    let l := line.trim
    if l.isEmpty then continue
    let H := parseHand l
    out := out ++ String.intercalate "," ((waits H).map (fun t => toString t.val)) ++ "\n"
  IO.FS.writeFile "../work/lean_hand_output.txt" out

#eval main
