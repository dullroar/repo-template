#!/usr/bin/env bash
# Step 4 of /prit: squash-merge the open PR of the current branch when its checks pass.
#
# Run me when: step 3 of /prit opened or found the PR, and the user wants it merged.
#
# Usage: prit-04-merge.sh
# Stops if checks fail or are pending, or if the PR has conflicts. It never bypasses protection
# (no --admin) and never deletes branches (step 5 does that).
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=prit-lib.sh
. "$here/prit-lib.sh"

in_repo
need_gh
require_work_branch
branch=$(current_branch)

n=$(open_pr_number "$branch")
[ -n "$n" ] || die "no open PR for $branch. Run prit-03-open-pr.sh first."

rc=0
out=$(gh pr checks "$n" 2>&1) || rc=$?
echo "$out"
case "$rc" in
  0) ;;
  8) die "checks of PR #$n are still pending. Run this script again when they finish." ;;
  *)
    if echo "$out" | grep -qi "no checks reported"; then
      echo "NOTE: PR #$n has no checks. Continuing."
    else
      die "checks of PR #$n failed. Fix them. This script does not bypass checks."
    fi
    ;;
esac

view=$(gh pr view "$n" --json state,mergeStateStatus -q '.state + " " + .mergeStateStatus')
case "$view" in
  *CONFLICTING* | *DIRTY*) die "PR #$n has merge conflicts ($view). Resolve them first." ;;
esac

gh pr merge "$n" --squash

state=$(gh pr view "$n" --json state -q .state)
[ "$state" = "MERGED" ] || die "PR #$n is in state $state after the merge call. Check it by hand."
echo "merge: PR #$n is MERGED (squash)"
