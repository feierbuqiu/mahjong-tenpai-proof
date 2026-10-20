# Contributing

Thank you for your interest. Corrections, questions, independent re-checks and improvements are all welcome.

## Ground rules

1. **Verified commits only.** A repository ruleset rejects any commit, on any branch, that GitHub does not mark as **Verified**. This applies to direct pushes and to pull requests alike.
   - Set up commit signing with an SSH or GPG key registered as a *signing key* on your GitHub account.
   - Commit with an email address verified on that account. GitHub's no-reply address is fine and keeps your email private.
   - Pull requests that contain unsigned commits cannot be merged; re-sign them (for example with `git rebase --exec 'git commit --amend --no-edit -S' <base>`) and force-push your branch.
2. **English.** Please write issues, pull requests and new documentation in English.
3. **Leave [`third_party/`](third_party/) unchanged.** It is an archival mirror of another author's work.
   - Do not edit, reformat or "fix" those files.
   - Report problems with that material in an issue instead.
   - Commentary belongs in [`docs/`](docs/) or in [`third_party/README.md`](third_party/README.md).
4. **Never commit personal data.** This includes:
   - absolute paths from your machine;
   - user names and email addresses;
   - access tokens;
   - session identifiers.

   Redact logs before committing them.

## Changing the Lean proof

The project lives in [`claude_independent_review/lean_formal/lean_project/`](claude_independent_review/lean_formal/lean_project/).

1. Keep the trusted specification [`Tenpai/Spec.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Spec.lean) minimal and faithful to the problem as defined in the [paper](claude_independent_review/Four_Tiles_Suffice_Lean_Verification_Paper.md) (Section 1.1). Any change to it needs a clear justification in the pull request.
2. Do not edit generated files by hand. The generated files are:
   - [`Tenpai/Data/*.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Data/);
   - [`Tenpai/Run/*.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Run/);
   - [`Tenpai/Main.lean`](claude_independent_review/lean_formal/lean_project/Tenpai/Main.lean).

   Regenerate them with the tools in [`claude_independent_review/lean_formal/tools/`](claude_independent_review/lean_formal/tools/) (see [`docs/reproducing.md`](docs/reproducing.md)). Continuous integration regenerates them on every change and fails if any file differs.
3. Run `lake build`. It must succeed, which includes the acceptance gate at the end of `Main.lean`. Continuous integration repeats this check on GitHub Actions for every change to the Lean sources.
4. If the sources change, record the new source manifest with [`tools/manifest.py`](claude_independent_review/lean_formal/tools/manifest.py). Update the digest wherever it is quoted ([`docs/reproducing.md`](docs/reproducing.md), the paper and the workflow template), and add the new build log under [`claude_independent_review/lean_formal/logs/`](claude_independent_review/lean_formal/logs/).

## Pull requests

- Describe what changes and why, and link the relevant issue if there is one.
- Keep each pull request focused on one change.
- Say which checks you ran and paste the relevant output, for example the `#print axioms` line and the source digest.

## Licence of contributions

By contributing, you agree that your contribution is licensed under the repository's [MIT Licence](LICENSE). Contributions to `third_party/` are not accepted.

## Conduct

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).
