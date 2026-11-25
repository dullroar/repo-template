#!/usr/bin/env bash
# Shared helpers for the prit-*.sh scripts.
#
# Run me when: never directly. The prit-*.sh scripts source it.
#
# Each helper prints one value or stops the caller with a clear error.

die() {
  echo "prit: $*" >&2
  exit 1
}

need_gh() {
  command -v gh >/dev/null 2>&1 || die "the gh command is not installed or not on PATH"
}

in_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a Git work tree"
}

current_branch() {
  git symbolic-ref --quiet --short HEAD || die "detached HEAD: check out a branch first"
}

# Default branch: origin/HEAD first, then the host, then main or master.
default_branch() {
  local ref b
  if ref=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null); then
    echo "${ref#origin/}"
    return 0
  fi
  if command -v gh >/dev/null 2>&1; then
    ref=$(gh repo view --json defaultBranchRef -q .defaultBranchRef.name 2>/dev/null || true)
    if [ -n "$ref" ]; then
      echo "$ref"
      return 0
    fi
  fi
  for b in main master; do
    if git show-ref --verify --quiet "refs/remotes/origin/$b"; then
      echo "$b"
      return 0
    fi
  done
  die "cannot find the default branch"
}

# Stop when the current branch is the default branch (never work or merge from it).
require_work_branch() {
  local branch def
  branch=$(current_branch)
  def=$(default_branch)
  [ "$branch" != "$def" ] || die "you are on the default branch '$def'. Create a branch first."
}

# Path of the main work tree (the first entry in the list).
primary_worktree() {
  git worktree list --porcelain | sed -n '1s/^worktree //p'
}

# True when this work tree is a linked work tree (not the main one).
is_linked_worktree() {
  [ "$(git rev-parse --git-dir)" != "$(git rev-parse --git-common-dir)" ]
}

# Number of the open PR for a branch, or nothing.
open_pr_number() {
  gh pr list --head "$1" --state open --json number -q '.[0].number // empty'
}

# Number of a merged PR for a branch, or nothing.
merged_pr_number() {
  gh pr list --head "$1" --state merged --json number -q '.[0].number // empty'
}
