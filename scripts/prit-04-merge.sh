#!/usr/bin/env bash
# Step 4 of /prit: squash-merge the open PR of the current branch when its checks pass.
#
# Run me when: step 3 of /prit opened or found the PR, and the user wants it merged.
#
# Usage: prit-04-merge.sh
# Uses the REST API only. Stops if checks fail or are pending, or if the PR has conflicts. It never bypasses protection
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

sha=$(git rev-parse HEAD)
remote_sha=$(gh api "repos/{owner}/{repo}/pulls/$n" --jq .head.sha)
[ "$sha" = "$remote_sha" ] || die "PR #$n head ($remote_sha) differs from the local HEAD ($sha). Push or pull first."

ci=$(ci_state "$sha")
echo "checks: $ci"
case "$ci" in
  pass) ;;
  none) echo "NOTE: PR #$n has no checks. Continuing." ;;
  pending) die "checks of PR #$n are still pending. Run this script again when they finish." ;;
  *) die "checks of PR #$n failed. Fix them. This script does not bypass checks." ;;
esac

# GitHub computes mergeability in the background. It can take a few seconds.
ms=null
for _ in 1 2 3 4 5; do
  ms=$(gh api "repos/{owner}/{repo}/pulls/$n" --jq '.mergeable_state // "null"')
  [ "$ms" != "unknown" ] && [ "$ms" != "null" ] && break
  sleep 2
done
echo "mergeable_state: $ms"
[ "$ms" != "dirty" ] || die "PR #$n has merge conflicts. Resolve them first."

gh api "repos/{owner}/{repo}/pulls/$n/merge" -X PUT -f merge_method=squash -f sha="$sha" --jq .message

merged=$(gh api "repos/{owner}/{repo}/pulls/$n" --jq .merged)
[ "$merged" = "true" ] || die "PR #$n is not merged after the merge call. Check it by hand."
echo "merge: PR #$n is MERGED (squash)"
