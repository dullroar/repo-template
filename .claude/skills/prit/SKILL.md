---
name: prit
description: Use only when the user says "PR it" or runs /prit. Commits are confirmed, then the branch is pushed, a PR is opened, the PR is squash-merged and the obsolete branches are deleted, one script at a time.
disable-model-invocation: true
---

# prit ("PR it")

The user said "PR it" or ran `/prit`. This is the authorization to push the current branch, open a PR, merge it and delete the merged branch. It applies to the current branch only.

Run the five steps in order. Run each script as its own command. Do not join scripts with `&&`, `;` or a pipe. Stop at the first script that exits with a non-zero code, show the user the message, and ask what to do. Never use `--force`, `--admin`, `--no-verify` or a different merge method.

Scripts are in `scripts/` of the repository. Run them from the work tree of the branch.

## 1. Confirm the branch is committed and current

Run `scripts/prit-01-check.sh`.

- Exit 0: go to step 2. If the output has a `NOTE:` line about "behind", merge `origin/<default>` into the branch, resolve any conflict with the user, and run the check again.
- Exit 3: the tree has uncommitted files. For each group (staged, unstaged, untracked), tell the user in plain words what the files are and recommend one action: commit, discard or stash. Wait for the answer. Then do what the user chose. Show the exact file list before any discard. Run the check again until it exits 0.
- A `PLAN-END candidate:` line: ask whether the plan is finished (the end of the whole plan, not of one step). If yes, run `git mv plans/<name> plans/archive/<name>`, then `python3 scripts/build_indexes.py` and `python3 scripts/check_context.py` if those scripts exist. Commit with the message `plan(<name>): archive`. Run the check again. If the repository has no `plans/` folder, skip this.

## 2. Push

Run `scripts/prit-02-push.sh`. It pushes only if needed and never forces.

## 3. Open the PR

Write the PR body to a temporary file outside the repository. Write a title of at most 80 characters.

The body must be short: aim for 1500 characters. The script rejects more than 4000. Use this form:

```text
## Summary
- <2 to 4 bullets: what changed>

## Why
<1 to 3 sentences>

## Plan
<path to the archived plan, if any>

## Verification
<commands that you ran and their result>

## Risks and follow-ups
<one line, or "none">
```

Do not copy the diff or the commit list. The reader has the diff, the history and the archived plan.

Run `scripts/prit-03-open-pr.sh "<title>" <body-file>`. Show the user the PR URL.

## 4. Merge

Run `scripts/prit-04-merge.sh`. It squash-merges when checks pass. If checks are pending or failed, or the PR has conflicts, report this and stop. Do not retry in a loop.

## 5. Clean up

Run `scripts/prit-05-cleanup.sh`.

- In a linked work tree it deletes the remote branch and stops. Ask the user before you run `scripts/prit-05-cleanup.sh --remove-worktree`.
- The script ends with a list of stale branch candidates. Show the list to the user. Delete a branch only after the user confirms it: `scripts/prit-05-cleanup.sh --also <branch>`.

## Finish

Report in a few lines: PR URL, merge result, branches deleted, branches left and why.
