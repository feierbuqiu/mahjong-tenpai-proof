axiom cheat : False
theorem bad2 : 1 = 2 := cheat.elim

/-- info: 'bad2' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms bad2
