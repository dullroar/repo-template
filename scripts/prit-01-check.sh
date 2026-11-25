#!/usr/bin/env bash
# Step 1 of /prit: report whether the current branch is committed and current. Changes nothing.
#
# Run me when: the user says "PR it" or runs /prit, as the first step, and again after you commit, discard or stash.
#
# Usage: prit-01-check.sh
# Exit 0: the tree is clean. Exit 3: the tree has uncommitted files (listed by group). Exit 1: error.
# Output lines "NOTE:" and "PLAN-END candidate:" are hints for the agent. Read them.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=prit-lib.sh
. "$here/prit-lib.sh"

in_repo
git fetch --quiet origin || die "git fetch failed"
require_work_branch
branch=$(current_branch)
def=$(default_branch)

echo "branch:   $branch"
echo "worktree: $(git rev-parse --show-toplevel)$(is_linked_worktree && echo ' (linked work tree)' || true)"
echo "default:  $def"

if upstream=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null); then
  echo "upstream: $upstream"
else
  echo "upstream: none (the branch is not pushed yet)"
fi

read -r ahead behind < <(git rev-list --left-right --count "HEAD...origin/$def")
echo "against origin/$def: $ahead ahead, $behind behind"
if [ "$behind" -gt 0 ]; then
  echo "NOTE: the branch is $behind commit(s) behind origin/$def. Merge origin/$def into the branch and run this check again."
fi
if [ "$ahead" -eq 0 ]; then
  echo "NOTE: the branch has no commit that origin/$def lacks. There may be nothing to open a PR for."
fi

# Plans whose steps are all done and that are not archived yet.
if [ -d plans ]; then
  for d in plans/*/; do
    name=$(basename "$d")
    case "$name" in archive | for-each-plan) continue ;; esac
    ls "$d"steps/*.md >/dev/null 2>&1 || continue
    if ! grep -h '^status:' "$d"steps/*.md | grep -qv 'done'; then
      echo "PLAN-END candidate: plans/$name (all steps are done; archive to plans/archive/$name if the plan is finished)"
    fi
  done
fi

status=$(git status --porcelain)
if [ -z "$status" ]; then
  echo "tree: clean"
  exit 0
fi

echo "tree: DIRTY"
echo "-- staged (index differs from HEAD):"
echo "$status" | awk '{x=substr($0,1,1); if (x!=" " && x!="?") print "   " $0}'
echo "-- unstaged (work tree differs from index):"
echo "$status" | awk '{x=substr($0,1,2); y=substr($0,2,1); if (y!=" " && x!="??") print "   " $0}'
echo "-- untracked:"
echo "$status" | awk 'substr($0,1,2)=="??" {print "   " $0}'
exit 3
