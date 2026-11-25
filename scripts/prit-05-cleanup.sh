#!/usr/bin/env bash
# Step 5 of /prit: delete the merged branch (remote and local), update the default branch, list other stale branches.
#
# Run me when: step 4 of /prit merged the PR, or the user asks to remove obsolete branches.
#
# Usage: prit-05-cleanup.sh [--remove-worktree] [--also <branch>]...
#   (no option)         delete the merged branch on the remote. In the main work tree, switch to the
#                       default branch, pull it, and delete the local branch. In a linked work tree,
#                       stop before removing the work tree and say how to finish.
#   --remove-worktree   in a linked work tree, remove it (never forced), then delete the local branch.
#                       Use this only after the user agrees.
#   --also <branch>     also delete this stale branch, local and remote. Use this only for branches
#                       that the user confirmed from the list this script prints.
# A branch is deleted only if its PR is merged. A squash merge leaves the branch "unmerged" for Git,
# so the script checks the PR on the host and then uses git branch -D.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=prit-lib.sh
. "$here/prit-lib.sh"

remove_wt=0
also=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --remove-worktree) remove_wt=1 ;;
    --also)
      [ "$#" -ge 2 ] || die "--also needs a branch name"
      also+=("$2")
      shift
      ;;
    *) die "unknown option: $1" ;;
  esac
  shift
done

in_repo
need_gh
git fetch --quiet --prune origin || die "git fetch failed"
def=$(default_branch)

# Delete a branch (remote and local) when its PR is merged and no PR is open.
delete_merged_branch() {
  local b=$1 rootdir=$2
  [ "$b" != "$def" ] || die "refusing to delete the default branch '$def'"
  [ -z "$(open_pr_number "$b")" ] || die "branch '$b' has an open PR. Not deleting."
  [ -n "$(merged_pr_number "$b")" ] || die "branch '$b' has no merged PR. Not deleting."
  if git show-ref --verify --quiet "refs/remotes/origin/$b"; then
    git push origin --delete "$b"
  fi
  if git show-ref --verify --quiet "refs/heads/$b"; then
    git -C "$rootdir" branch -D "$b"
  fi
}

branch=$(current_branch)
[ "$branch" != "$def" ] || die "you are on the default branch '$def'. Run this from the merged branch."
[ -n "$(merged_pr_number "$branch")" ] || die "branch '$branch' has no merged PR. Run prit-04-merge.sh first."
[ -z "$(git status --porcelain)" ] || die "the tree is dirty. Resolve the files first."

if is_linked_worktree; then
  wt=$(git rev-parse --show-toplevel)
  primary=$(primary_worktree)
  [ -z "$(open_pr_number "$branch")" ] || die "branch '$branch' has an open PR."
  if git show-ref --verify --quiet "refs/remotes/origin/$branch"; then
    git push origin --delete "$branch"
  fi
  if [ "$(git -C "$primary" symbolic-ref --quiet --short HEAD || true)" = "$def" ]; then
    git -C "$primary" pull --ff-only --quiet origin "$def"
  else
    echo "NOTE: the main work tree ($primary) is not on '$def'. Not updated."
  fi
  if [ "$remove_wt" -eq 1 ]; then
    cd "$primary"
    git worktree remove "$wt"
    git branch -D "$branch"
    echo "cleanup: removed work tree $wt and branch $branch. Your shell may still be in the removed folder: cd $primary"
  else
    echo "LINKED WORK TREE: $wt"
    echo "The remote branch is deleted. To finish, ask the user, then run: prit-05-cleanup.sh --remove-worktree"
    echo "(or by hand: git -C $primary worktree remove $wt && git -C $primary branch -D $branch)"
  fi
else
  root=$(git rev-parse --show-toplevel)
  git checkout "$def"
  git pull --ff-only --quiet origin "$def"
  delete_merged_branch "$branch" "$root"
  echo "cleanup: deleted $branch (remote and local). Now on $def."
fi

# Extra branches the user confirmed.
for b in ${also[@]+"${also[@]}"}; do
  delete_merged_branch "$b" "$(primary_worktree)"
  echo "cleanup: deleted $b"
done

# List other stale branches for the user to decide on. Nothing is deleted here.
echo "-- stale branch candidates (ask the user; delete only with --also <branch>):"
found=0
while read -r name track; do
  [ "$name" = "$def" ] && continue
  case "$track" in *gone*)
    echo "   local $name (its remote branch is gone)"
    found=1
    ;;
  esac
done < <(git for-each-ref --format='%(refname:short) %(upstream:track)' refs/heads)
while read -r name; do
  b=${name#origin/}
  [ "$b" = "$def" ] || [ "$b" = "HEAD" ] || [ "$name" = "origin" ] && continue
  if [ -z "$(open_pr_number "$b")" ] && [ -n "$(merged_pr_number "$b")" ]; then
    echo "   remote $b (its PR is merged)"
    found=1
  fi
done < <(git for-each-ref --format='%(refname:short)' refs/remotes/origin)
[ "$found" -eq 1 ] || echo "   none"
