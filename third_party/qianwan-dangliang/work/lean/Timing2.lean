import Mj.Upper2
open Mj

def bigBlocks (n thr : Nat) : List Nat :=
  ((blocks.filter (fun r =>
    let (_, c1, s1, k1, c2, s2, k2) := decRec r
    (xsLookup c1 s1 (keyEnc (keyOf c1 s1 k1))).length *
    (xsLookup c2 s2 (keyEnc (keyOf c2 s2 k2))).length >= thr)).take n)

def main : IO Unit := do
  IO.println s!"nIIBlocks={nIIBlocks} nIIUnitsTotal={nIIUnitsTotal} nIIProfiles={nIIProfiles}"
  IO.println s!"profTable groups={profTable.length} blocks.length={blocks.length} profTableOk={profTableOk}"
  let t0 ← IO.monoMsNow
  let a := checkBlocks (blocks.take 1000)
  let t1 ← IO.monoMsNow
  IO.println s!"[A] first 1000 blocks: blocks={a.1} failed={a.2.1} units={a.2.2}  {t1 - t0} ms"
  let t2 ← IO.monoMsNow
  let b := checkBlocks (bigBlocks 200 300)
  let t3 ← IO.monoMsNow
  IO.println s!"[B] 200 biggest-ish blocks (units>=300): blocks={b.1} failed={b.2.1} units={b.2.2}  {t3 - t2} ms"
  let t4 ← IO.monoMsNow
  let c := checkBlocks (blocks.take 20000)
  let t5 ← IO.monoMsNow
  IO.println s!"[C] first 20000 blocks: blocks={c.1} failed={c.2.1} units={c.2.2}  {t5 - t4} ms"
