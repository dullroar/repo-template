# Goal: adopt the pinned controls in repo-template

## Ralph loop prompt

Use this prompt for each loop iteration. It has no chat history, so keep it complete.

> You work on plan `adopt-controls` in this repository. Read `AGENTS.md`, then `plans/adopt-controls/goal.md` and `plan.md`.
> Open the step file you were given. Work only in the worktree you were given, on its branch.
> Do only that step. Change only the files in `touches`.
> Run the full unit test suite and the `gate` command. If one fails, find the cause and fix it. Do not weaken or delete the gate.
> When the gate passes, set `status: done` and write `evidence` (command, result, date). Commit.
> If you cannot finish, keep `status: in_progress`, write what remains under "Resume notes" in the step file, and commit.
> If you are blocked, set `status: blocked` and write the reason. Do not guess.
> Never push, publish, change a remote or change a GitHub setting. Never run `ralph-pusher`.
> Never write secrets or personal data in any file. Write in Simplified Technical English.

## Goal

This repository is `repo-template`. Every new repository starts as a copy of it. This plan gives the template the pinned `deterministic-controls` library, a blocking secret guard, the agent rules for controls and routing, and the routing fields in the plan template. After this plan, a new repository has the same checks in the developer shell, in the hooks and in CI.

The library is `v0.1.0` at a pinned commit. Install line:

`python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@651543baf8d308ec4e0ca0e69fb12a52fb0d6848"`

## Done when

- `python3 scripts/check_context.py` passes. It runs the pinned library through a shim.
- `python3 -m unittest discover -s tests -v` passes. It includes the smoke test on a fresh copy and on an old copy of the template.
- The secret guard runs in CI (`--tracked`, and `--range` on pull requests) and in the pre-commit and pre-push hooks.
- A plan step without `gate` fails with the `plans.schema` rule ID.
- `docs/controls-adoption.md` has the receipt and the rollback.
- Every step of this plan is `done` with evidence.

## Out of scope

- Any repository other than this one. Pushing, publishing, changing a remote or a GitHub setting.
- Required checks and branch protection. The operator does that later.
- Changes to the pinned library.
