#!/usr/bin/env bash
# Install the prit SKILL.md in the user skill folders of Claude Code and Codex (and the Windows profile in WSL).
#
# Run me when: I want /prit in every repository on this machine, and after I change the skill.
#
# Usage: prit-install-user.sh [--dry-run]
# Targets: ~/.claude/skills/prit and ~/.codex/skills/prit. In WSL it also finds %USERPROFILE% and does the
# same there. A target folder is made only if its parent (for example ~/.codex/skills) exists.
# It overwrites an older copy of SKILL.md in a prit folder only. It never touches other skills.
# The user copy holds only SKILL.md. The repository must have scripts/prit-*.sh.
set -euo pipefail
here=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
skill="$here/../.agents/skills/prit/SKILL.md"
[ -f "$skill" ] || { echo "prit-install-user: $skill not found" >&2; exit 1; }

dry=0
case "${1:-}" in
  "") ;;
  --dry-run) dry=1 ;;
  *) echo "usage: prit-install-user.sh [--dry-run]" >&2; exit 1 ;;
esac

homes=("$HOME")
if grep -qi microsoft /proc/version 2>/dev/null && command -v cmd.exe >/dev/null 2>&1 && command -v wslpath >/dev/null 2>&1; then
  win=$(cmd.exe /c "echo %USERPROFILE%" 2>/dev/null | tr -d '\r' || true)
  if [ -n "$win" ] && wp=$(wslpath -u "$win" 2>/dev/null) && [ -d "$wp" ]; then
    homes+=("$wp")
  fi
fi

for h in "${homes[@]}"; do
  for agent in .claude .codex; do
    parent="$h/$agent/skills"
    if [ ! -d "$parent" ]; then
      echo "skip:   $parent (no such folder)"
      continue
    fi
    target="$parent/prit/SKILL.md"
    if [ -f "$target" ] && cmp -s "$skill" "$target"; then
      echo "same:   $target"
    elif [ "$dry" -eq 1 ]; then
      echo "would copy: $target"
    else
      mkdir -p "$parent/prit"
      cp "$skill" "$target"
      echo "copied: $target"
    fi
  done
done
