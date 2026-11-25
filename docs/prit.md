# prit: "PR it"

`/prit` takes the current branch from "work done" to "merged". It replaces one long chained command with five small scripts. An agent runs them one at a time and stops between them to ask you questions.

A skill does not bypass permission checks. The gain is that each step is one simple command. You can review it, allow it by name, and the agent pauses at each decision.

## How to use it

- Claude Code: type `/prit`.
- Codex: ask for the `prit` skill, or say "PR it".

The skill has two real copies: `.agents/skills/prit/SKILL.md` (Codex) and `.claude/skills/prit/SKILL.md` (Claude Code). There is no symbolic link, because links fail on some Windows checkouts. `.agents/skills/prit/SKILL.md` is the master. After you edit it, copy it to the other place. A test fails if the two differ.

## Steps

| Step | Script | What it does |
| --- | --- | --- |
| 1 | `scripts/prit-01-check.sh` | Shows branch, work tree, upstream and uncommitted files. Changes nothing. Exit 3 means the tree is dirty. |
| 2 | `scripts/prit-02-push.sh` | Pushes the branch if needed. Never forces. |
| 3 | `scripts/prit-03-open-pr.sh` | Opens a PR, or shows the open one. Rejects a body over 4000 characters. |
| 4 | `scripts/prit-04-merge.sh` | Squash-merges when checks pass. Never bypasses protection. |
| 5 | `scripts/prit-05-cleanup.sh` | Deletes the merged branch (remote and local) and lists stale branches. |

## Why REST

The scripts use only the REST API (`gh api`), never `gh pr ...`. Those commands use the GraphQL API. GraphQL had an outage while REST kept working. One path is easier to test than a main path and a fallback.

## Rules that the agent follows

- At step 1, the agent summarizes each group of uncommitted files and recommends commit, discard or stash. You decide.
- At the end of a whole plan (not one step), the agent archives the plan to `plans/archive/<name>/` and commits it. The archive is then part of the PR.
- A PR body is short. The diff, the history and the archived plan carry the detail.
- Squash merge leaves the local branch "unmerged" for Git. Step 5 checks the PR on the host, then uses `git branch -D`.
- In a linked work tree, step 5 deletes the remote branch and asks before it removes the work tree.

## Limits of PR text

| Host | Limit of the PR description | prit limit |
| --- | --- | --- |
| Azure DevOps | 4000 characters | 4000 |
| GitHub | 65536 characters | 4000 (the same, to stay portable) |

The target is 1500 characters.

## Not supported yet

- Azure DevOps. Steps 3 to 5 call the GitHub REST API with `gh api`. A host check in `scripts/prit-lib.sh` and calls to `az repos pr` are the work to do.
- Conflict resolution. The scripts stop and report.

## Install in another repository

Run `scripts/prit-install-into.sh <path-of-repository>`. It copies the skill (both copies) and the scripts, and it never overwrites a different file.

## Install for your user account

Run `scripts/prit-install-user.sh`. It copies `SKILL.md` to the user skill folders of Claude Code (`~/.claude/skills/prit`) and Codex (`~/.codex/skills/prit`). In WSL it also does this for the Windows profile (`%USERPROFILE%`). Use `--dry-run` to see the targets. The user copy holds only `SKILL.md`. It needs the `scripts/prit-*.sh` files in the repository where you run it.
