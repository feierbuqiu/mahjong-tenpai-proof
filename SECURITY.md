# Security Policy

This repository's main product is a machine-checked proof. Its security therefore means keeping the published result **sound**, keeping the published files **intact**, and keeping contributors' data **private**.

## What to report

1. **Soundness problems.** Any way in which `lake build` in [`claude_independent_review/lean_formal/lean_project/`](claude_independent_review/lean_formal/lean_project/) could succeed even though:
   - `Tenpai.kStar_eq_four` does not hold for the specification in [`Tenpai/Spec.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Spec.lean), or
   - its axiom set differs from `[propext, Classical.choice, Quot.sound]`.

   For example, a flaw in the acceptance gate, or an option or construct that bypasses kernel checking.
2. **Specification problems.** A place where `Tenpai/Spec.lean` does not faithfully express the problem statement in [`docs/problem-statement.md`](docs/problem-statement.md).
3. **Integrity problems.** These include:
   - files that do not match the source manifest recorded in [`claude_independent_review/lean_formal/logs/`](claude_independent_review/lean_formal/logs/) or the checksums in [`third_party/qianwan-dangliang.SHA256SUMS`](third_party/qianwan-dangliang.SHA256SUMS);
   - commits that are not shown as Verified.
4. **Privacy problems.** Personal data or machine-specific information that should not have been published.

## How to report

- **Sensitive reports:** please use GitHub's **private vulnerability reporting** (the *Report a vulnerability* button on the repository's *Security* tab).
- **Non-sensitive reports:** for example a disagreement with the specification. Opening a normal issue is fine.

Please include:
- what you observed;
- the exact commit;
- the commands you ran;
- the relevant output.

## Supported versions

Only the latest commit on the default branch (`main`) is maintained.

## Commit integrity

Every commit on every branch of this repository must carry a signature that GitHub verifies. Unsigned or unverifiable commits are rejected by a repository ruleset with no bypass, for pushes and for pull-request merges alike.

## Third-party code

The programs in [`third_party/`](third_party/) are mirrored as they were published by their author. They contain absolute paths from the author's own machine, and the repository author has not reviewed them for safe execution. Read them before running them, and run them only in an isolated environment.
