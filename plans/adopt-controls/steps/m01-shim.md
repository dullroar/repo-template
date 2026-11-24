---
id: m01-shim
status: pending
depends_on: [m00-secret-guard]
touches:
  - scripts/check_context.py
  - scripts/controls-requirements.txt
  - controls.toml
  - scripts/AGENTS.md
  - docs/controls-adoption.md
  - .github/workflows/context.yml
  - plans/adopt-controls/steps/m01-shim.md
lane: none
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && grep -q '651543baf8d308ec4e0ca0e69fb12a52fb0d6848' scripts/controls-requirements.txt && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Adopt the pinned library with `adopt apply`

This is the first real use of the adoption tools. Record each place where they did not fit in `docs/controls-adoption.md`, under "Where the tools did not fit". That text goes to the lessons of the program.

## Change

- Install the pinned library into a temporary virtual environment outside the repository (install line in `plan.md`). Run `adopt audit`, then `adopt plan` (a dry run), then `adopt apply`. Run `apply` before any other edit, because it needs a clean tree. Keep the commit on this step branch.
- Result: `scripts/check_context.py` is the shim. `scripts/controls-requirements.txt` has the pinned install line. `controls.toml` exists. `docs/controls-adoption.md` describes the adoption.
- The shim keeps the old output lines (`ok  <script>` or `FAIL <script>`) and the exit codes `0` and `1`. It gives exit `2` if the library cannot run. It never passes without a result.
- Keep `scripts/build_indexes.py`. Keep the old scripts `check_plan.py`, `check_links.py`, `scan_secrets.py` and `ctx_common.py`. Step `m04` deletes them after it proves equivalence.
- `apply` may write a `controls` job into `.github/workflows/context.yml`. Keep the `check` job, its steps from `m00` and the workflow name `context`. If `apply` writes any other file outside `touches`, revert that file, and record it under "Where the tools did not fit".
- Add the shim and the new files to `scripts/AGENTS.md` with `python3 scripts/build_indexes.py`.

## Do not change

- Files outside `touches`. The `gate` command.
- Do not make the shim fall back to the old scripts.

## Already done by earlier steps

- m00-secret-guard: the secret guard, the hooks, the guard tests and the CI steps.

## Done when

- The gate passes. `python3 scripts/check_context.py` prints the old output lines and runs the library.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
