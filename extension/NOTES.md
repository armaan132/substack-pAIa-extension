# Notes — browser extension (`extension/`)

## What this is

A self-contained **Chrome (Manifest V3) browser extension** that re-ranks a
Substack feed from the user's own read / like / hide feedback, entirely
on-device. It's the "Option B" in-page re-ranker described in
[`docs/roadmap.md`](../docs/roadmap.md).

## It is isolated by design — it does not touch the rest of the repo

Everything the extension needs lives inside this `extension/` folder:

- Plain static assets only: `*.js`, `*.css`, `*.html`, `manifest.json`, PNG icons.
- **No build step, no dependencies, no package manager.**
- It does **not** import from, run, or modify the Python project at the repo root
  (`src/`, `nlp-scripts/`, `scripts/`, `requirements.txt`, the `test_*.py` files).
- It does **not** read or write anything outside the browser: all state lives in
  `chrome.storage.local` (with a `localStorage` fallback used only by the test
  harness). Nothing leaves the device.
- Its `test/` file is a **plain HTML page**, not a Python test — `pytest` and the
  root test suite ignore it.

You can add, run, or refactor the Python code freely without affecting this
folder, and vice versa.

## Files

| File | Role |
|------|------|
| `manifest.json` | MV3 manifest (permissions: `storage`; hosts: `*.substack.com`) |
| `engine.js` | Ranking engine — publication + author affinity, freshness (pure functions) |
| `store.js` | Storage adapter (`chrome.storage.local`, falls back to `localStorage`) |
| `content.js` | Scrape → inject feedback bar → re-rank the feed in place |
| `content.css` | Styles for the injected UI (all classes are `paia-` prefixed) |
| `background.js` | Service worker: default settings + toolbar badge |
| `popup.html` / `popup.js` / `popup.css` | Dashboard (counts, affinity, top ranked) |
| `icons/` | Toolbar icons (16/48/128) |
| `test/test-feed.html` | Mock Substack feed for verifying the pipeline in a plain browser |
| `README.md` | How it works + install steps |
| `ROADMAP.md` | 5-week plan (mirror of `docs/roadmap.md`) |

## Try it

**Load into Chrome:** `chrome://extensions` → enable **Developer mode** →
**Load unpacked** → select this `extension/` folder → open a Substack feed.

**Or verify without Substack** (mock feed, no login):

```sh
cd extension
python3 -m http.server 4175
# open http://localhost:4175/test/test-feed.html
```

## Status

Prototype (v0.1). Verified end-to-end against the mock feed. Live Substack DOM
selectors still need tuning — see the "Known limitations" in `README.md` and
Week 1 of `ROADMAP.md`.
