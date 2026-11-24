---
id: m03-ci
status: pending
depends_on: [m01-shim]
touches:
  - .github/workflows/context.yml
  - tests/test_workflow.py
  - plans/adopt-controls/steps/m03-ci.md
lane: none
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && python3 scripts/secret_guard.py --tracked && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Make the CI job pinned, read-only and stable

## Change

- `.github/workflows/context.yml`: the job name is `context` (the stable name for required checks). Triggers: `pull_request`, `push` to `main` and `workflow_dispatch`. No path filters. `permissions: contents: read`. Pin every action to a full 40-character commit SHA, with the tag in a trailing comment (find it with `git ls-remote --tags`). Install the library from `scripts/controls-requirements.txt`. Run the `ci` profile: `python3 -m deterministic_controls check --root . --profile ci --format json --report "$RUNNER_TEMP/controls.json"`. Upload the report with `actions/upload-artifact`. No `continue-on-error`. The check must fail the job on any nonzero exit.
- Keep the steps of `m00`: `fetch-depth: 0`, the secret guard on all tracked files and, for pull requests, on the commit range. Keep the old `python3 scripts/check_context.py` step only if it adds a check that the `ci` profile does not give. Else remove it.
- `tests/test_workflow.py`: read the workflow as text. Assert: no `uses:` line without a 40-character SHA, `permissions: contents: read` is present, there is no `paths:` filter, no `continue-on-error`, the job name is `context`, and the guard steps exist. Test each rule with a bad sample text that fails and with the real file that passes.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- m00-secret-guard: the guard steps. m01-shim: `controls.toml`, the pin file and the shim.

## Done when

- The gate passes. The workflow test fails on each bad sample for the expected reason.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
