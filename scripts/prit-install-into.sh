#!/usr/bin/env bash
# Install the prit skill and its scripts into another repository. Never overwrites a different file.
#
# Run me when: I want to add the /prit skill to an existing repository (do it on a branch in that repository).
#
# Usage: prit-install-into.sh <path-of-target-repository>
# Copies: .agents/skills/prit/SKILL.md, scripts/prit-*.sh, docs/prit.md. Creates the link .claude/skills
# (to ../.agents/skills) and plans/archive/.gitkeep when they are absent. Safe to run twice.
# Exit 1 if a target file exists and differs, or the target is not a Git work tree. Nothing is copied then.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
src=$(cd "$here/.." && pwd)

[ "$#" -eq 1 ] || { echo "usage: prit-install-into.sh <target-repo>" >&2; exit 1; }
dst=$(cd "$1" && pwd) || { echo "prit-install: no such folder: $1" >&2; exit 1; }
git -C "$dst" rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "prit-install: not a Git work tree: $dst" >&2; exit 1; }
[ "$dst" != "$src" ] || { echo "prit-install: the target is the source repository" >&2; exit 1; }

files=(.agents/skills/prit/SKILL.md docs/prit.md)
for f in "$src"/scripts/prit-*.sh; do files+=("scripts/$(basename "$f")"); done

conflicts=0
for f in "${files[@]}"; do
  if [ -e "$dst/$f" ] && ! cmp -s "$src/$f" "$dst/$f"; then
    echo "CONFLICT: $f exists in the target and differs" >&2
    conflicts=1
  fi
done
if [ -e "$dst/.claude/skills" ] || [ -L "$dst/.claude/skills" ]; then
  if [ "$(readlink "$dst/.claude/skills" 2>/dev/null || true)" != "../.agents/skills" ]; then
    echo "CONFLICT: .claude/skills exists in the target and is not a link to ../.agents/skills" >&2
    conflicts=1
  fi
fi
[ "$conflicts" -eq 0 ] || exit 1

for f in "${files[@]}"; do
  if [ -e "$dst/$f" ]; then
    echo "same:   $f"
  else
    mkdir -p "$dst/$(dirname "$f")"
    cp -p "$src/$f" "$dst/$f"
    echo "copied: $f"
  fi
done
if [ ! -e "$dst/.claude/skills" ] && [ ! -L "$dst/.claude/skills" ]; then
  mkdir -p "$dst/.claude"
  ln -s ../.agents/skills "$dst/.claude/skills"
  echo "linked: .claude/skills"
fi
if [ ! -e "$dst/plans/archive" ]; then
  mkdir -p "$dst/plans/archive"
  touch "$dst/plans/archive/.gitkeep"
  echo "made:   plans/archive/.gitkeep"
fi

cat <<'MSG'
Next, by hand in the target repository:
- If it has AGENTS.md: add to the rule about pushing: 'When the user says "PR it" or runs /prit, that is
  authorization to push the current branch, open a PR, merge it and delete the merged branch. See docs/prit.md.'
- If it has scripts/build_indexes.py: run it, then run the checks of the repository.
MSG
