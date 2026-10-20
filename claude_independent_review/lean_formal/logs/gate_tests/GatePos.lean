theorem good (p : Prop) [Decidable p] : p ∨ ¬p := Classical.em p

/-- info: 'good' depends on axioms: [propext, Classical.choice, Quot.sound] -/
#guard_msgs in
#print axioms good
