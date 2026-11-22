# DISPOSABLE: this script only proves the template works (Windows Sandbox, PowerShell, paths).
# DELETE it, and hello-listing.sh, in every repo created from this template.
#
# Run me when: I want to prove the PowerShell or Windows Sandbox setup works. (Template only.)
$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
Write-Output "Repository root: $root"
Get-ChildItem -Force -Path $root | ForEach-Object { $_.Name }
