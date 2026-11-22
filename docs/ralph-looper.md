# Running a plan with ralph-looper

`ralph-looper` is a separate repository (`dullroar/ralph-looper`). It runs the steps of a plan with a coding agent. It works with any repository that uses the plan layout in [AGENTS.md](../AGENTS.md).

## Why a separate repository

- One copy of the loop code. A fix applies to all repositories.
- A repository can still change the behavior. Add an optional `plans/<plan>/loop.yaml`.

## Where files go

| What | Where | Tracked? |
| --- | --- | --- |
| Goal, plan, steps, step status | `plans/<plan>/` | Yes |
| Output log, usage records, locks, pause flags | `~/repo-work/<repo>/<plan>/` | No |
| Git worktrees of the plan | `~/repo-work/<repo>/<plan>/worktrees/` | No |

On Windows, use `%USERPROFILE%\repo-work\<repo>\<plan>\`.

## How a run works

1. The loop makes a branch `plan/<plan>`.
2. It picks a ready step. A step is ready when all steps in `depends_on` are done.
3. It makes a worktree and a branch for the step. An agent works there.
4. The agent runs the step `gate` command and records `evidence`.
5. The loop merges the step into `plan/<plan>`.
6. The loop writes a usage block to `driver.out` (agent, model, tokens, cost where known).

## Stop and restart

- You can stop the loop at any time, for example with a crash, a kill or an empty token budget.
- All state is in Git (step files) and in `~/repo-work`. No state is in chat.
- Start the loop again with any agent. It reclaims old claims and continues the unfinished step.
