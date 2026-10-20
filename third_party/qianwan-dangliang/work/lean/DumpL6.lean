import Mj.Upper2
open Mj

def main : IO Unit := do
  for s in l6BatchStats do
    IO.println (toString s.1 ++ " " ++ toString s.2.1 ++ " " ++ toString s.2.2.1 ++ " " ++ toString s.2.2.2)
  IO.println ("TOTAL " ++ toString l6Total.1 ++ " " ++ toString l6Total.2.1 ++ " " ++
              toString l6Total.2.2.1 ++ " " ++ toString l6Total.2.2.2)
