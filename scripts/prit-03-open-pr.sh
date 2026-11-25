#!/usr/bin/env bash
# Step 3 of /prit: open a pull request for the current branch, or show the one that is open.
#
# Run me when: step 2 of /prit pushed the branch, and you have a PR title and a PR body file.
#
# Usage: prit-03-open-pr.sh <title> <body-file>
# The body file must not be longer than 4000 characters (the limit of Azure DevOps; GitHub allows more).
# If a PR is open for the branch, this script prints its URL and does not change it.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=prit-lib.sh
. "$here/prit-lib.sh"

BODY_MAX=4000
TITLE_MAX=200

[ "$#" -eq 2 ] || die "usage: prit-03-open-pr.sh <title> <body-file>"
title=$1
body_file=$2

in_repo
need_gh
require_work_branch
branch=$(current_branch)
def=$(default_branch)

[ -n "$title" ] || die "the title is empty"
[ "${#title}" -le "$TITLE_MAX" ] || die "the title has ${#title} characters. The limit is $TITLE_MAX."
[ -f "$body_file" ] || die "body file not found: $body_file"
size=$(wc -m <"$body_file" | tr -d ' ')
[ "$size" -gt 0 ] || die "the body file is empty"
[ "$size" -le "$BODY_MAX" ] || die "the body has $size characters. The limit is $BODY_MAX. Shorten it. The diff and the archived plan carry the detail."

git fetch --quiet origin || die "git fetch failed"
git show-ref --verify --quiet "refs/remotes/origin/$branch" || die "origin/$branch does not exist. Run prit-02-push.sh first."
[ "$(git rev-parse HEAD)" = "$(git rev-parse "origin/$branch")" ] || die "the branch and origin/$branch differ. Run prit-02-push.sh first."

existing=$(open_pr_number "$branch")
if [ -n "$existing" ]; then
  echo "pr: PR #$existing is already open for $branch. Not changed."
  gh pr view "$existing" --json url -q .url
  exit 0
fi

gh pr create --base "$def" --head "$branch" --title "$title" --body-file "$body_file"
