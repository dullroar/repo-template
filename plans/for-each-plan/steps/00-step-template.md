---
id: 00-step-template
status: pending
depends_on: []
touches:
  - path/or/glob/this/step/will/change
lane: none
gate: exact command that proves this step is complete
# Optional routing keys. Remove the "#" to use one. Old plans do not need them.
# agent: script | claude | codex | copilot | operator
# fallback: the agent to use if the first agent cannot do the step
# run: the command that a script step runs
# tier: light
# acceptance_controls: [check-id-1, check-id-2]
#   Use IDs from the catalog: python3 -m deterministic_controls list
claimed_by: ""
claimed_at: ""
evidence: ""
---

# <One sentence: the goal of this step>

Write for an agent that has no chat history. Size the step so that a small model can do it.

<!--
Operator-step example. An operator step needs a human action.
Use these front-matter values:

  agent: operator
  lane: none
  gate: test -s plans/<plan-name>/records/<action>.md && grep -q "^approved-on: " plans/<plan-name>/records/<action>.md

The operator writes the record file. The gate proves the human action in that
file. Do not write a secret or a personal name in the record.
-->

## Change

- `path`: the change to make.

## Do not change

- Files outside `touches`. The `gate` command.

## Already done by earlier steps

- <step id: what it gives you>

## Done when

- <An observable result.>

## Record

Set `status: done`. Fill `evidence` with the gate command, the result and the date.
If you cannot finish, write "Resume notes" below. Keep the status `in_progress`.

## Resume notes

(none)
