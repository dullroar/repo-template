---
id: m04-smoke
status: pending
depends_on: [m01-shim, m02-agent-rules, m03-ci]
touches:
  - tests/test_template_smoke.py
  - docs/controls-adoption.md
  - scripts/check_plan.py
  - scripts/check_links.py
  - scripts/scan_secrets.py
  - scripts/ctx_common.py
  - scripts/AGENTS.md
  - plans/adopt-controls/steps/m04-smoke.md
lane: none
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/build_indexes.py --check && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Prove the library on a fresh copy and an old copy, then delete the old checks

## Change

- `tests/test_template_smoke.py`: copy the template tree (tracked files of `HEAD`, from `git archive`) into a temporary directory as a new Git repository, with one commit. Run `python3 scripts/check_context.py` there. It passes. Add a plan step that has no `gate`. The run now fails with exit `1` and the rule ID `plans.schema` in the output. Remove the step. It passes again.
- The old copy: the template tree at the commit before this plan. Find it as the parent of the first commit that added `plans/adopt-controls/goal.md` (`git log --diff-filter=A --format=%H -- plans/adopt-controls/goal.md`). Copy it into a temporary Git repository. Run the old `check_context.py` and note the result. Run `adopt apply` there with the pinned library (the same install line as in `plan.md`). Run the new shim. The result and the exit codes must match, for the clean tree and for the same known-bad plan.
- The tests need the network once for the cached library. If the library is not available, skip with the message `library not available` and not a pass. Do not skip when the cache exists.
- Do not assert a literal version. Assert behavior and exit codes.
- Delete the old check scripts that the library replaced (`scripts/check_plan.py`, `scripts/check_links.py`, `scripts/scan_secrets.py`) only if the equivalence tests passed. Delete `scripts/ctx_common.py` only if no remaining script imports it (`scripts/build_indexes.py` may). Keep `scripts/build_indexes.py` and the shim. Update `scripts/AGENTS.md` with `python3 scripts/build_indexes.py`. Search the repository for text that mentions a deleted script, and fix it if the file is in `touches`. Record in `docs/controls-adoption.md` each script deleted, and each script kept with the reason.
- If the results differ, keep the old scripts and record the difference in `docs/controls-adoption.md`. Set the step to `blocked` with the facts.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- m01-shim: the shim and the pin. m02-agent-rules: the plan template fields. m03-ci: the workflow and its test.

## Done when

- The gate passes. The known-bad plan fails with `plans.schema` in a fresh copy and in an old copy after `adopt apply`.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
