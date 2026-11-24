---
gist: "Read me when: you adopt the pinned deterministic-controls library, the secret guard, the agent rules for controls and routing, and the routing fields in repo-template."
---

# Plan: adopt the pinned controls in repo-template

This file is the high-level plan. The detail is in `steps/`. Every step is self-contained. Read this file for the shared facts.

## Approach

Every new repository starts as a copy of this template. So the controls go here first. Each later repository then gets the same checks from its first commit.

The template has these check scripts in `scripts/`: `check_context.py` (runs the others), `check_plan.py`, `check_links.py`, `scan_secrets.py`, `build_indexes.py` and `ctx_common.py`. The library `deterministic-controls` replaces the checks. `scripts/check_context.py` becomes a shim that runs the library. The shim keeps the old output lines and exit codes. `scripts/build_indexes.py` stays: it writes the indexes. The old check scripts stay until the smoke test (m04) proves that the library gives the same result. Then m04 deletes them.

## Facts

- Library: `deterministic-controls` `v0.1.0`. Install line: `python3 -m pip install "deterministic-controls @ git+https://github.com/dullroar/deterministic-controls@651543baf8d308ec4e0ca0e69fb12a52fb0d6848"`.
- Commands: `python3 -m deterministic_controls {list,check,explain,version,adopt}`. `adopt` has `audit`, `plan`, `apply` and `receipt`. `check --root DIR --profile quick|ci|full [--format text|json] [--report FILE]`. Exit codes: `0` pass, `1` defects, `2` bad configuration, invocation or no result, `3` internal error. Use `--help` for the details.
- The shim runs the library from a cached virtual environment for the pinned commit, under `$XDG_CACHE_HOME/deterministic-controls/<commit>/` (default `~/.cache/...`). It creates the environment on first use. This needs the network once for each pinned commit. If it cannot, it fails with exit `2` and a clear message. It never falls back to the old scripts and never passes without a result.
- `adopt apply` works only on a clean tree and on the current branch. It never pushes. It is idempotent. Run it before any other edit of the step.
- A fixture file that holds Markdown has the extra suffix `.fixture` (for example `README.md.fixture`). The test copies the fixture to a temporary directory and removes the suffix. Build a fixture that holds a secret at run time. Never store it as a file.
- Do not compare wheel digests or literal versions in tests. Assert behavior.
- Run the full unit test suite (`python3 -m unittest discover -s tests -v`) before each commit, not only the test file of the step. Find every test that the step makes obsolete and fix it, if it is in `touches`.

## Steps

| Step | Executor | Goal | Depends on |
| --- | --- | --- | --- |
| [m00-secret-guard](./steps/m00-secret-guard.md) | cloud agent, light | Secret guard, hooks and a blocking CI step. | none |
| [m01-shim](./steps/m01-shim.md) | cloud agent | Adopt the pinned library with `adopt apply`. Keep the old scripts. | m00 |
| [m02-agent-rules](./steps/m02-agent-rules.md) | cloud agent | Agent rules for controls and routing. Plan template fields. | m00 |
| [m03-ci](./steps/m03-ci.md) | cloud agent | Pinned, read-only CI job with a stable name. | m01 |
| [m04-smoke](./steps/m04-smoke.md) | cloud agent | Fresh-copy and old-copy smoke tests. Delete the old check scripts. | m01, m02, m03 |
| [m05-verify](./steps/m05-verify.md) | cloud agent, light | Clean-clone verification and receipt. | m04 |

## Parallelism

- `m00` runs first. The secret guard must be in the first commit.
- `m01` and `m02` run together. `m01` touches the scripts, `controls.toml` and the CI file. `m02` touches `AGENTS.md`, the plan template and `docs/routing.md`.
- `m03`, `m04` and `m05` run one after the other.

## Risks

- **A secret is committed.** `m00` installs the guard first. Do not add an exception to pass a step. A new exception needs a reason and a fingerprint, and the owner reviews it.
- **The shim cannot get the library (no network).** Write that under "Resume notes" and stop. Do not change the gate. Do not use the old scripts as a replacement.
- **The old scripts and the library differ.** `m04` runs both on the same fixtures. It deletes the old scripts only if the results match. Else it records the difference and keeps the scripts.
- **A new template field breaks an old plan.** `m02` adds only optional keys. `m04` checks that an old plan still passes.
