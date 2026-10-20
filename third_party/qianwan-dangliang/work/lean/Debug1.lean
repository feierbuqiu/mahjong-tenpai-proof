import Mj.Basic
import Mj.Data
namespace Mj
def encCode (c : List Nat) : Nat := c.foldl (fun acc t => acc * 34 + t) 0
def allCodeNats : List Nat := planData.foldl (fun acc p => acc ++ p.2.map encCode) []
end Mj
#eval (Mj.planData.take 1).map (fun p => p.2.map Mj.encCode)
#eval (Mj.allCodeNats.filter (fun x => x == 1)).length
#eval (Mj.allCodeNats.filter (fun x => x == 2)).length
#eval (Mj.planData.filter (fun p => p.2.contains [0,0,0,1])).length
#eval (Mj.planData.filter (fun p => p.2.contains [0,1,1,2])).length
#eval (Mj.planData.map (fun p => p.2.length)).sum
#eval (Mj.planData.take 1).map (fun p => p.2.length)
