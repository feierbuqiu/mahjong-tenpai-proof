## What this changes

<!-- What changes and why. Link the issue if there is one. -->

## Checklist

- [ ] Every commit is signed and shows as **Verified** (unsigned commits are rejected on every branch).
- [ ] No file under `third_party/` was modified.
- [ ] No personal data was added: no absolute paths, user names, email addresses, tokens or session identifiers.
- [ ] Generated Lean files (`Tenpai/Data/`, `Tenpai/Run/`, `Tenpai/Main.lean`) were regenerated with the tools, not edited by hand.
- [ ] If Lean sources changed:
  - [ ] `lake build` succeeds, including the acceptance gate;
  - [ ] the new source digest is recorded;
  - [ ] the build log is added under `claude_independent_review/lean_formal/logs/`.
- [ ] Documentation is in English.

## Checks run

<!-- Paste the relevant output, e.g. the `#print axioms` line and the source digest. -->
