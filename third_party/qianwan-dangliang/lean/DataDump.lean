import Mj.Data
open Mj

def keyStr (k : List Nat) : String := String.intercalate "," (k.map toString)
def rowStr (p : List Nat × List (List Nat)) : String :=
  keyStr p.1 ++ "|" ++ String.intercalate ";" (p.2.map (fun c => String.intercalate "," (c.map toString)))

def main : IO Unit := do
  IO.FS.writeFile "../work/lean_plandata_dump.txt" (String.intercalate "\n" (planData.map rowStr) ++ "\n")

#eval! main
