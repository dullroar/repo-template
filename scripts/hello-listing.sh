#!/usr/bin/env bash
# DISPOSABLE: this script only proves the template works (Dockerfile, shell, paths).
# DELETE it, and hello-listing.ps1, in every repo created from this template.
#
# Run me when: I want to prove the container or shell setup works. (Template only.)
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "Repository root: ${root}"
ls -1A "${root}"
