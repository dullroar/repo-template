# Controls adoption

This repository uses the library `deterministic-controls`. The library is pinned to one commit in `scripts/controls-requirements.txt`. The file `controls.toml` lists the enabled checks.

## How it works

- `scripts/check_context.py` is a shim. It runs the library from a cached virtual environment for the pinned commit.
- The cache is under `$XDG_CACHE_HOME/deterministic-controls/<commit>/`. The default is `~/.cache/deterministic-controls/<commit>/`.
- The first run for a commit needs the network. If the library cannot run, the shim exits with `2`. It never passes without a result. It never uses the old scripts instead.
- The shim prints `ok  <script>` or `FAIL <script>` for each group of checks. Exit `0` means pass. Exit `1` means a check failed.
- `scripts/build_indexes.py` stays. It writes the indexes.
- The old scripts `check_plan.py`, `check_links.py`, `scan_secrets.py` and `ctx_common.py` stay for now. Step `m04` of the plan `adopt-controls` deletes them after it proves that the results are the same.

## How the adoption was made

1. `adopt audit` classified the repository as partial. The shim, the pin, the manifest and the CI job were missing.
2. `adopt plan` showed a dry run.
3. `adopt apply` wrote the workflow job, `controls.toml`, the shim and the pin. It ran on a clean tree, on the step branch.

## Where the tools did not fit

- `adopt plan` needs `--commit`. The command help of `audit` gives no hint about it. Pass the pinned commit.
- `adopt apply` did not write `docs/controls-adoption.md`. This file was written by hand.
- The step text says to install the library in a virtual environment. The session had no network and no install right. The operator put the pinned release on `PYTHONPATH` instead.
- `apply` added a `controls` job to `.github/workflows/context.yml`. The job repeats the secret guard steps from `m00`. The `check` job stays.
- The shim needs the network on its first run for a commit. A machine without network cannot run the gate until the cache exists.
