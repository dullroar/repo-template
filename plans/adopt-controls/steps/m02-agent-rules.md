---
id: m02-agent-rules
status: pending
depends_on: [m00-secret-guard]
touches:
  - AGENTS.md
  - plans/for-each-plan/**
  - plans/AGENTS.md
  - docs/routing.md
  - docs/README.md
  - plans/adopt-controls/steps/m02-agent-rules.md
lane: none
gate: python3 -m unittest discover -s tests -v && python3 scripts/check_context.py && for key in agent fallback run tier acceptance_controls; do grep -q "$key" plans/for-each-plan/steps/00-step-template.md || exit 1; done && grep -qi 'operator' plans/for-each-plan/steps/00-step-template.md && grep -q 'disable' AGENTS.md && test -s docs/routing.md && grep -q 'routing.md' docs/README.md && git diff --check
claimed_by: ""
claimed_at: ""
evidence: ""
---

# Add the agent rules for controls and routing, and the plan template fields

## Change

- `AGENTS.md`, in the standing rules or in a new section: the agent may run the local checks. CI runs them in all cases. The agent must not change or disable the controls, the pin (`scripts/controls-requirements.txt`), `controls.toml` or the workflows to make an unrelated task pass. The driver checks the gate and `touches` of each step. Keep the file in Simplified Technical English. Keep all existing rules.
- `docs/routing.md`: a short routing policy, in Simplified Technical English. Content: send each piece of work to the cheapest executor that can do it. The gate decides if the work is done. Routes: checks, builds, index generation, imports and measurements go to a `script` step or a CI job (no model). Design, tricky parsers, migrations, adjudication and review go to a cloud agent (`claude`, `codex` or `copilot`). Small checks of recorded results go to a cloud agent with `tier: light`. Many independent text transformations go to the Batch API tool, run by the operator. Approvals, publication, settings, credentials and native-speaker review go to an `operator` step. The merge decision belongs to CI and the protected branch. Prefer `script` when the work is deterministic. A `script` gate must prove the output, not only the exit code. An `operator` gate must prove the human action in a file or record. Agents have no credentials and cannot push. The local model is not used in this program. Add a link to the full policy: `https://github.com/dullroar/ralph-looper/blob/main/docs/routing.md`.
- `docs/README.md`: add one line for `routing.md`.
- `plans/for-each-plan/steps/00-step-template.md`: add the optional keys `agent`, `fallback`, `run`, `tier` and `acceptance_controls` (check IDs from the library catalog, from `python3 -m deterministic_controls list`). Add them as comments or empty values that the plan check accepts. Add an operator-step example: a second file in the same folder, or a clear comment block, that shows `agent: operator` and a gate that proves the human action.
- Old plans must still pass. Add only optional keys.

## Do not change

- Files outside `touches`. The `gate` command.
- Do not change the `gist` of a plan that is listed in `plans/AGENTS.md`, unless you run `python3 scripts/build_indexes.py` and the changed index is in `touches`.

## Already done by earlier steps

- m00-secret-guard: the guard, the hooks and the tests in `tests/`.

## Done when

- The gate passes.

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
