import Mj.Upper2

open Mj

/-- 把列表按 n 切段 -/
def chunkBy (n : Nat) (xs : List Nat) : List (List Nat) :=
  let rec go (fuel : Nat) (ys : List Nat) : List (List Nat) :=
    match fuel with
    | 0 => []
    | f + 1 => if ys.isEmpty then [] else (ys.take n) :: go f (ys.drop n)
  go (xs.length / n + 2) xs

def doneLines (path : System.FilePath) : IO Nat := do
  if ← path.pathExists then
    let s ← IO.FS.readFile path
    return (s.splitOn "\n").filter (fun l => !l.isEmpty) |>.length
  else
    return 0

def jsonLine (idx nb fb nu fu ms : Nat) : String :=
  "{\"batch\": " ++ toString idx ++ ", \"blocks\": " ++ toString nb ++
  ", \"failed_blocks\": " ++ toString fb ++ ", \"units\": " ++ toString nu ++
  ", \"failed_units\": " ++ toString fu ++ ", \"ms\": " ++ toString ms ++ "}"

def main (args : List String) : IO Unit := do
  let batchSize : Nat := (args.head?.bind (fun s => s.toNat?)).getD 20000
  let progress : System.FilePath := "D:/DSH/MJ2/work/lean/gen_data2_progress.jsonl"
  let start ← doneLines progress
  let chunks := chunkBy batchSize blocks
  IO.println ("blocks=" ++ toString blocks.length ++ " batchSize=" ++ toString batchSize ++
              " batches=" ++ toString chunks.length ++ " resumeFrom=" ++ toString start)
  let mut idx := 0
  for ch in chunks do
    if idx >= start then
      let t0 ← IO.monoMsNow
      let (nb, fb, nu, fu) := batchStat ch
      let t1 ← IO.monoMsNow
      let line := jsonLine idx nb fb nu fu (t1 - t0)
      IO.FS.withFile progress IO.FS.Mode.append (fun h => h.putStrLn line)
      IO.println line
    idx := idx + 1
  IO.println "DONE"
