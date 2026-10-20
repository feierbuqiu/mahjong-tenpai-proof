import Mj.Basic
open Mj
def dumpHand (H : Hand) : String :=
  String.intercalate "," (H.v.toList.map toString)
def dump (l : List Hand) : IO Unit := do
  let mut s := ""
  for H in l do
    s := s ++ dumpHand H ++ "|" ++ String.intercalate "," ((waits H).map (fun t => toString t.val)) ++ "\n"
  IO.FS.writeFile "../work/lean_waits_sample.txt" s
def main : IO Unit := do
  -- 单花色前 1500 手 + 随机带字牌的手牌 500 手（用确定性取样）
  dump ((flushHands.take 1500) ++ (handsIn [0,8,9,17,18,26,27,28,29,30,31,32,33] 13).take 500)
#eval main
