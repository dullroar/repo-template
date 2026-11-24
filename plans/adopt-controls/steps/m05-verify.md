---
id: m05-verify
status: pending
depends_on: [m04-smoke]
touches:
  - docs/controls-adoption.md
  - docs/README.md
  - plans/adopt-controls/steps/m05-verify.md
lane: none
tier: light
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && grep -q 'rollback' docs/controls-adoption.md && grep -q 'controls-adoption.md' docs/README.md && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Verify from a clean clone and write the receipt

## Change

- Clone this worktree into a temporary directory outside the repository. Run these there: `python3 -m unittest discover -s tests -v`, `python3 scripts/check_context.py`, `python3 scripts/build_indexes.py --check`, `python3 scripts/secret_guard.py --tracked`, `python3 scripts/secret_guard.py --history`, `bash scripts/install_hooks.sh --self-test`. Record each command, its result, the test count and the UTC date in `docs/controls-adoption.md`. Record the count of `--history` findings.
- Write the receipt with `python3 -m deterministic_controls adopt receipt` (use the cached or a temporary environment of the pinned library). Put it in `docs/controls-adoption.md` as a JSON block.
- Test and record the rollback. Set the previous pin in `scripts/controls-requirements.txt` (or the pre-adoption scripts from the base commit), run the check, and record that it gives the same pass result on the clean tree. Then restore the pin. Write the steps under the heading "Rollback".
- Add one line for `controls-adoption.md` to `docs/README.md`.
- Add to `docs/controls-adoption.md` a list of each secret guard exception (`.secret-guard-allow` entry or inline allow) that this plan added. Write `none` if there is none.

## Do not change

- Files outside `touches`. The `gate` command. The pin in the final commit.

## Already done by earlier steps

- m04-smoke: the smoke tests, and the deleted old scripts.

## Done when

- The gate passes. The receipt, the rollback and the clean-clone results are in `docs/controls-adoption.md`.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
