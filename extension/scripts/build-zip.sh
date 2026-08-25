#!/usr/bin/env bash
# Build the Chrome Web Store submission zip: only the files the extension runs.
# Excludes tests, node_modules, scripts, store assets, docs, and dev config.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

OUT="store/daily-briefing-paia.zip"
mkdir -p store
rm -f "$OUT"

FILES=(
  manifest.json
  engine.js
  store.js
  content.js
  content.css
  background.js
  popup.html
  popup.js
  popup.css
  options.html
  options.js
  options.css
  icons/icon16.png
  icons/icon48.png
  icons/icon128.png
)

# verify each file exists before zipping
for f in "${FILES[@]}"; do
  [ -f "$f" ] || { echo "MISSING: $f" >&2; exit 1; }
done

zip -q "$OUT" "${FILES[@]}"
echo "Built $OUT"
unzip -l "$OUT" | tail -n +2
