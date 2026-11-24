# Routing policy

Send each piece of work to the cheapest executor that can do it. The gate decides if the work is done.

Full policy: <https://github.com/dullroar/ralph-looper/blob/main/docs/routing.md>

## Routes

| Work | Executor |
| --- | --- |
| Checks, builds, index generation, imports, measurements | A `script` step or a CI job. No model. |
| Design, tricky parsers, migrations, adjudication, review | A cloud agent: `claude`, `codex` or `copilot`. |
| Small checks of recorded results | A cloud agent with `tier: light`. |
| Many independent text transformations | The Batch API tool, run by the operator. |
| Approvals, publication, settings, credentials, native-speaker review | An `operator` step. |
| The merge decision | CI and the protected branch. |

## Rules

1. Prefer `script` when the work is deterministic.
2. A `script` gate must prove the output, not only the exit code.
3. An `operator` gate must prove the human action in a file or a record.
4. Agents have no credentials. Agents cannot push.
5. The local model is not used in this program.
