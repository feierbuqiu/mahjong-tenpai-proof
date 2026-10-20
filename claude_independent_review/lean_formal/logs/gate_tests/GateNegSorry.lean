theorem bad : 1 = 2 := sorry

/-- info: 'bad' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms bad
