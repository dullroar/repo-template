# Controls adoption

This repository uses the library `deterministic-controls`. The library is pinned to one commit in `scripts/controls-requirements.txt`. The file `controls.toml` lists the enabled checks.

## How it works

- `scripts/check_context.py` is a shim. It runs the library from a cached virtual environment for the pinned commit.
- The cache is under `$XDG_CACHE_HOME/deterministic-controls/<commit>/`. The default is `~/.cache/deterministic-controls/<commit>/`.
- The first run for a commit needs the network. If the library cannot run, the shim exits with `2`. It never passes without a result. It never uses the old scripts instead.
- The shim prints `ok  <script>` or `FAIL <script>` for each group of checks. Exit `0` means pass. Exit `1` means a check failed.
- `scripts/build_indexes.py` stays. It writes the indexes.
- The shim still prints the old script names (`check_plan.py`, `check_links.py`, `scan_secrets.py`) as group labels. The scripts themselves are deleted. See "Old scripts" below.

## How the adoption was made

1. `adopt audit` classified the repository as partial. The shim, the pin, the manifest and the CI job were missing.
2. `adopt plan` showed a dry run.
3. `adopt apply` wrote the workflow job, `controls.toml`, the shim and the pin. It ran on a clean tree, on the step branch.

## Smoke test and old scripts

The test `tests/test_template_smoke.py` proves that the library gives the same result as the old scripts:

- Fresh copy: the tracked files of `HEAD` in a new Git repository. The check passes. A plan step without `gate` makes it fail with exit `1` and the rule ID `plans.schema`. After the step is removed, it passes again.
- Old copy: the template tree before this plan, in a new Git repository. The old scripts pass on the clean tree and fail (exit `1`) on the same bad plan. After `adopt apply` and the new shim, the exit codes are the same, and the library reports `plans.schema`.
- The shim prints only the group names. The test reads the rule ID from the JSON output of the library.
- If the library is not available (no network and no cache), the tests skip with `library not available`.

Old scripts, after the equivalence tests passed:

| Script | Result | Reason |
| --- | --- | --- |
| `scripts/check_plan.py` | deleted | The library checks `plans.schema` and `plans.graph`. |
| `scripts/check_links.py` | deleted | The library checks `markdown.local-links`. |
| `scripts/scan_secrets.py` | deleted | The library checks `security.secrets` and `security.personal-data`. |
| `scripts/ctx_common.py` | kept | `scripts/build_indexes.py` imports it. |
| `scripts/build_indexes.py` | kept | It writes the indexes. The library does not write them. |
| `scripts/check_context.py` | kept | It is the shim. |

One gap: `adopt apply` writes `scripts/controls-requirements.txt` without a `Run me when:` line. `scripts/build_indexes.py` then fails. The test adds the line by hand, as step `m01` did.

## Where the tools did not fit

- `adopt plan` needs `--commit`. The command help of `audit` gives no hint about it. Pass the pinned commit.
- `adopt apply` did not write `docs/controls-adoption.md`. This file was written by hand.
- The step text says to install the library in a virtual environment. The session had no network and no install right. The operator put the pinned release on `PYTHONPATH` instead.
- `apply` added a `controls` job to `.github/workflows/context.yml`. The job repeats the secret guard steps from `m00`. The `check` job stays.
- The shim needs the network on its first run for a commit. A machine without network cannot run the gate until the cache exists.

## Clean-clone verification

Date (UTC): 2026-11-24. The repository was cloned with `git clone` into a new temporary directory outside the repository. This was the base commit `c299a0a` (the merge of `m04-smoke`). The library came from the cached environment of the pinned commit.

| Command | Result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | pass, 31 tests, 0 failures |
| `python3 scripts/check_context.py` | pass, exit `0` |
| `python3 scripts/build_indexes.py --check` | pass, no output |
| `python3 scripts/secret_guard.py --tracked` | pass, 0 findings |
| `python3 scripts/secret_guard.py --history` | pass, 0 findings |
| `bash scripts/install_hooks.sh --self-test` | pass, `install_hooks self-test: ok` |

The count of `--history` findings is 0.

## Receipt

The command `python3 -m deterministic_controls adopt receipt --root <clone> --commit 651543baf8d308ec4e0ca0e69fb12a52fb0d6848` wrote this receipt. The `repository` value is the name of the temporary clone directory.

```json
{
  "base_revision": "c299a0a3aa14eb9b41ec4851dd0f083a09bd3ce6",
  "checks_run": [
    {"check_id": "context.index-freshness", "status": "passed"},
    {"check_id": "markdown.local-links", "status": "passed"},
    {"check_id": "plans.graph", "status": "passed"},
    {"check_id": "plans.schema", "status": "passed"},
    {"check_id": "repo.forbidden-artifacts", "status": "passed"},
    {"check_id": "security.personal-data", "status": "passed"},
    {"check_id": "security.secrets", "status": "passed"}
  ],
  "commands_kept": [
    "scripts/build_indexes.py",
    "scripts/ctx_common.py",
    "scripts/hello-listing.ps1",
    "scripts/hello-listing.sh",
    "test: python3 -m unittest discover -s tests",
    "test: docker build (Dockerfile)",
    "ci-job: context"
  ],
  "control_pin": "651543baf8d308ec4e0ca0e69fb12a52fb0d6848",
  "date": "2026-11-24",
  "enabled_checks": [
    "context.index-freshness",
    "markdown.local-links",
    "plans.graph",
    "plans.schema",
    "repo.forbidden-artifacts",
    "security.personal-data",
    "security.secrets"
  ],
  "enforcement_state": "advisory",
  "files_added": [],
  "files_changed": [],
  "profile": "ci",
  "repository": "m05-clean-clone",
  "schema_version": 1
}
```

The receipt shows `enforcement_state: advisory`. The operator makes the check required later (see "Out of scope" in the plan).

## Rollback

There is no earlier pin. The adoption added the first pin (commit `88cfe72`). So the rollback test used the pre-adoption scripts from the parent commit `9fa033c`.

Test, on 2026-11-24 (UTC):

1. Clone the repository. Check out `88cfe72^` (`9fa033c`).
2. Run the old `scripts/check_context.py` from that commit. The scripts check the current directory, so they checked the clean tree of the step worktree. It printed `ok` for `build_indexes.py`, `check_plan.py`, `check_links.py` and `scan_secrets.py`. Result: pass.
3. Run the new shim on the same clean tree. Result: pass.
4. The pass result is the same. The pin in `scripts/controls-requirements.txt` was not changed in the working tree, so no restore was needed.

Steps to roll back:

1. To use another pin: edit the install line in `scripts/controls-requirements.txt`. Put the other commit in it. Run `python3 scripts/check_context.py` once. It builds a new cached environment for that commit.
2. To remove the adoption: use `git revert` on the adoption commits, on a new branch. Or restore the files from the base commit with `git checkout <commit> -- <file>`. The adoption added `scripts/check_context.py` (shim), `scripts/controls-requirements.txt`, `controls.toml`, `scripts/secret_guard.py`, `scripts/install_hooks.sh` and `.github/workflows/context.yml`. The adoption deleted `scripts/check_plan.py`, `scripts/check_links.py` and `scripts/scan_secrets.py`. Restore them from `88cfe72^`.
3. Run `python3 scripts/check_context.py` and `python3 -m unittest discover -s tests -v`.
4. The cached environment is under `$XDG_CACHE_HOME/deterministic-controls/<commit>/`. It is safe to delete.

## Secret guard exceptions

This plan added these exceptions (`.secret-guard-allow` entries and inline allows): none.
