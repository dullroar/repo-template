#!/usr/bin/env bash
# Step 2 of /prit: push the current branch to origin if it is not there yet. Never forces.
#
# Run me when: step 1 of /prit reported a clean tree, and the branch is not on the remote or has new commits.
#
# Usage: prit-02-push.sh
# Stops with exit 1 if the tree is dirty, if the remote branch has commits that are not here, or on the default branch.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=prit-lib.sh
. "$here/prit-lib.sh"

in_repo
require_work_branch
branch=$(current_branch)
[ -z "$(git status --porcelain)" ] || die "the tree is dirty. Run prit-01-check.sh and resolve the files first."
git fetch --quiet origin || die "git fetch failed"

if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
  read -r ahead behind < <(git rev-list --left-right --count "HEAD...origin/$branch")
  [ "$behind" -eq 0 ] || die "origin/$branch has $behind commit(s) that this branch lacks. Merge or rebase by hand. This script never forces."
  if [ "$ahead" -eq 0 ]; then
    git branch --set-upstream-to="origin/$branch" "$branch" >/dev/null
    echo "push: origin/$branch is already up to date. Nothing to push."
    exit 0
  fi
fi

git push --set-upstream origin "HEAD:refs/heads/$branch"
echo "push: done ($branch)"
