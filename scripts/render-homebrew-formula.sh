#!/usr/bin/env bash
# Render homebrew/til.rb.template into a concrete Formula/til.rb for the
# kfet/homebrew-til tap.
#
# Usage: scripts/render-homebrew-formula.sh <VERSION> <OUT_FILE>
#
# VERSION is the bare semver (no leading "v").
set -euo pipefail

VERSION="${1:?version required}"
OUT="${2:?output path required}"

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
tmpl="${repo_root}/homebrew/til.rb.template"
[ -f "$tmpl" ] || { echo "missing template: $tmpl" >&2; exit 1; }

mkdir -p "$(dirname -- "$OUT")"
sed -e "s/__VERSION__/${VERSION}/g" "$tmpl" > "$OUT"

if command -v ruby >/dev/null 2>&1; then
  ruby -c "$OUT" >/dev/null
fi

echo "✓ rendered $OUT (til $VERSION)"
