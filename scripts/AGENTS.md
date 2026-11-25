# Scripts index

<!-- IMMUTABLE HEADER: do not edit the text above the BEGIN marker. -->

This folder holds deterministic scripts for agents and CI: run, test, debug and build. CI scripts start here.

- Each script starts with a comment block that has a line `Run me when: <situation>` in its first 25 lines.
- Scripts must give the same result for the same input. Print clear errors and use exit code 0 only for success.
- Never put secrets or personal paths in a script. Read them from the environment.
- This file is generated. Run `python3 scripts/build_indexes.py` after any change. Do not edit the list below by hand.

Read the list. Run only the scripts whose "Run me when" line matches your task.

<!-- BEGIN GENERATED INDEX -->

* [build_indexes.py](./build_indexes.py)
  Run me when: I added, renamed, deleted or changed the gist of a memory, a plan or a script, and before every pull request.
* [check_context.py](./check_context.py)
  Run me when: I changed any context file, and before every pull request.
* [controls-requirements.txt](./controls-requirements.txt)
  Run me when: I change the pinned version of the controls library.
* [ctx_common.py](./ctx_common.py)
  Run me when: never directly. Other scripts in this folder import it.
* [hello-listing.ps1](./hello-listing.ps1)
  Run me when: I want to prove the PowerShell or Windows Sandbox setup works. (Template only.)
* [hello-listing.sh](./hello-listing.sh)
  Run me when: I want to prove the container or shell setup works. (Template only.)
* [install_hooks.sh](./install_hooks.sh)
  Run me when: I cloned a repository, or the hooks are missing (check with --check).
* [prit-01-check.sh](./prit-01-check.sh)
  Run me when: the user says "PR it" or runs /prit, as the first step, and again after you commit, discard or stash.
* [prit-02-push.sh](./prit-02-push.sh)
  Run me when: step 1 of /prit reported a clean tree, and the branch is not on the remote or has new commits.
* [prit-03-open-pr.sh](./prit-03-open-pr.sh)
  Run me when: step 2 of /prit pushed the branch, and you have a PR title and a PR body file.
* [prit-04-merge.sh](./prit-04-merge.sh)
  Run me when: step 3 of /prit opened or found the PR, and the user wants it merged.
* [prit-05-cleanup.sh](./prit-05-cleanup.sh)
  Run me when: step 4 of /prit merged the PR, or the user asks to remove obsolete branches.
* [prit-install-into.sh](./prit-install-into.sh)
  Run me when: I want to add the /prit skill to an existing repository (do it on a branch in that repository).
* [prit-install-user.sh](./prit-install-user.sh)
  Run me when: I want /prit in every repository on this machine, and after I change the skill.
* [prit-lib.sh](./prit-lib.sh)
  Run me when: never directly. The prit-*.sh scripts source it.
* [secret_guard.py](./secret_guard.py)
  Run me when: before a commit or a push (the hooks do it), in CI, before a merge, or to audit a repository for secrets.

<!-- END GENERATED INDEX -->
