# Daily Briefing pAIa — 5-Week Roadmap to the Chrome Web Store

**Objective:** ship a small, single-purpose Chrome extension that re-ranks your
Substack feed from your own read / like / hide feedback, entirely on-device.

## Approach — single-user, content-based

This is a **single-user, content-based recommender that runs entirely on your
device.** It builds a taste profile from *your own* history — the posts you read,
liked, and hid — and ranks new posts by similarity to that profile
(publication + author affinity + freshness, which the engine already does).

- No other users, no shared model, no backend, no accounts.
- Your history and taste profile never leave the browser (`chrome.storage.local`).
- No cold-start problem: it only ever needs your own signals to work.

Multi-user collaborative filtering ("people who read X also read Y") is a
different, server-based product and is **explicitly out of scope** here — see
[Not in scope](#not-in-scope-for-this-product).

A 5-week plan from the current prototype (v0.1) to a submitted v1.0. Each week is
a phase with concrete tasks and an **exit criteria** gate — testing is baked into
every week, with a dedicated hardening week (Week 4) before submission.

**Assumptions:** ~10–15 focused hours/week, one developer. If time is tighter,
the *Stretch* items in each week are the first to cut. A one-week buffer isn't
built in, so treat aggressive weeks (1 and 4) as the risk points.

Legend: ✅ done · ◻️ todo · ⭑ stretch

---

## Phase 0 — Prototype (v0.1) ✅ *done*

- ✅ MV3 scaffold (manifest, service worker, content script, popup)
- ✅ Ranking engine (publication + author affinity, freshness, per-post bumps)
- ✅ Scrape → inject feedback bar → re-rank in place
- ✅ Floating panel (re-rank toggle, sort, restore original order)
- ✅ Popup dashboard (counts, affinity bars, top ranked)
- ✅ Local storage + mock-feed test harness; fixed the rapid-click race

---

## Week 1 — Real Substack integration (v0.2)

The single biggest risk. The scraper works on a mock; make it survive the live site.

- ◻️ Map the live DOM for the two surfaces most people use: `substack.com/home`
  and `/inbox`
- ◻️ Harden `scrape()` / `pickTitle` / `pickAuthor` / `pickDate` against real markup
- ◻️ Solid card-container detection (don't grab nav, footer, or "recommended" links)
- ◻️ Handle infinite scroll without duplicate injection or a runaway
  MutationObserver ↔ reorder loop
- ◻️ Inert on non-feed pages (single post, settings)
- ◻️ Save 1–2 real pages as HTML fixtures in `test/` for offline regression
- ⭑ Also support a publication `*.substack.com/archive` page

**Testing gate:** open your own feed logged in & out; bars appear, re-rank works,
zero duplicate bars on scroll, no console errors, no layout breakage.

**Exit:** works on `/home` and `/inbox` without hand-editing selectors per visit.

---

## Week 2 — Core features (v0.3–0.4)

Make it genuinely useful, not just a demo.

- ◻️ **Auto-read detection** (scroll depth + dwell time), still manually overridable
- ◻️ **"Why this rank?"** tooltip per card (engine already returns `reasons`)
- ◻️ **Undo hide** + a "show hidden" control
- ◻️ First-run/empty states in the popup and panel
- ⭑ **Category/tag affinity** in addition to publication + author
- ⭑ Minimal **options**: toggle auto-read, toggle which surfaces it runs on

**Testing gate:** a short manual script per feature; re-run Week 1's gate to
confirm nothing regressed.

**Exit:** you'd comfortably use it yourself day to day.

---

## Week 3 — Resilience & accessibility (v0.5)

- ◻️ Storage schema version + a migration path (so future changes don't wipe data)
- ◻️ Quota / write-failure handling — never break the feed on a storage error
- ◻️ Export / import signals (JSON) + a confirmed "reset all"
- ◻️ Accessibility: injected controls keyboard-reachable, labeled (ARIA),
  contrast passes, respects `prefers-reduced-motion`
- ◻️ Visual QA in Substack light **and** dark themes, narrow/wide windows
- ⭑ `chrome.storage.sync` option with a local fallback

**Testing gate:** migrate a v0.1 storage blob without loss; keyboard-only run of
all controls; both themes clean.

**Exit:** no data-loss paths; a keyboard user can operate everything.

---

## Week 4 — Testing & hardening (v0.9)

The QA week. Automate what's cheap; manually verify the rest.

- ◻️ **Unit tests** for `engine.js` (Vitest/Jest): weights, affinity roll-up,
  scoring, freshness, ranking order, the race scenario
- ◻️ **DOM/integration tests** for `content.js` against the saved fixtures (jsdom):
  scrape correctness, injection, reorder, restore-original
- ◻️ Lint + format (ESLint/Prettier)
- ◻️ **Performance:** no jank on a large feed; MutationObserver doesn't leak
  (heap snapshot over a 5-min scroll)
- ◻️ **Robustness:** no uncaught errors anywhere; degrade quietly on selector miss
- ◻️ CSP clean; confirm **no remote code** (hard Web Store rule)
- ⭑ One Playwright E2E loading the unpacked extension against a fixture

**Testing gate:** the full [pre-submission checklist](#pre-submission-checklist)
passes; engine unit tests green.

**Exit:** the checklist is green end to end.

---

## Week 5 — Store submission (v1.0)

- ◻️ **Permissions audit** — keep it minimal (`storage` + `*.substack.com`),
  write the justification for each
- ◻️ **Privacy policy** (short: "stores your feedback locally, collects nothing")
  hosted at a URL
- ◻️ **Single-purpose** statement for the listing
- ◻️ Listing assets: 128px icon, 1–3 screenshots (1280×800), promo tile,
  description
- ◻️ Register Chrome Web Store developer account ($5 one-time)
- ◻️ Bump version, zip the folder, upload, submit for review
- ◻️ Respond to review feedback; publish

**Exit:** submitted (and ideally approved — review can take a few days, so submit
early in the week).

---

## Pre-submission checklist

Run in full before packaging (Week 4 gate).

### Functional
- ◻️ Feedback bar on every real feed card; buttons toggle correctly
- ◻️ Re-rank reorders by score; "Original order" restores exactly
- ◻️ Hide + undo works
- ◻️ Rapid multi-click doesn't drop signals (race regression)
- ◻️ Popup matches on-page state (counts, affinity, top ranked)
- ◻️ Settings persist across page loads and a browser restart
- ◻️ Toolbar badge reflects liked count

### Substack surfaces
- ◻️ `/home` and `/inbox`, logged in & out
- ◻️ Infinite scroll: no duplicates, no runaway re-render
- ◻️ Non-feed pages stay inert

### Robustness & performance
- ◻️ Zero uncaught console errors on tested pages
- ◻️ Degrades gracefully when a selector matches nothing
- ◻️ No memory growth over a 5-minute scroll (heap snapshot)
- ◻️ No visible jank scrolling a large feed

### Accessibility & visual
- ◻️ Controls keyboard-operable and labeled (ARIA)
- ◻️ Contrast passes; works in light and dark Substack themes
- ◻️ Respects `prefers-reduced-motion`

### Store policy
- ◻️ Single purpose clearly holds
- ◻️ Minimal permissions, each justified
- ◻️ No remote code / no eval / no external scripts
- ◻️ Privacy policy accurate (collects nothing)
- ◻️ Manifest validates; version bumped

### Packaging
- ◻️ Load-unpacked smoke test on a clean Chrome profile
- ◻️ Zipped build installs cleanly

---

## Schedule at a glance

| Week | Version | Focus | Main risk |
|------|---------|-------|-----------|
| 0 ✅ | 0.1 | Prototype verified on mock | — |
| 1 | 0.2 | Live Substack scraping | **High** — DOM fragility |
| 2 | 0.3–0.4 | Auto-read, tooltip, undo | Medium |
| 3 | 0.5 | Resilience, a11y, themes | Low |
| 4 | 0.9 | Tests + hardening | **Medium-high** |
| 5 | 1.0 | Store listing + submit | Low (review latency) |

**If a week slips:** cut ⭑ stretch items first, then defer category affinity and
`storage.sync` to a post-launch v1.1. Weeks 1 and 4 are where to protect time.

## Explicitly post-launch (v1.1+)

Enhancements that still fit the single-user, on-device model — kept out of the 5
weeks so the scope stays shippable: category/tag affinity (if not reached),
semantic/embedding-based similarity, cross-device sync of *your own* data via
`chrome.storage.sync`, full E2E suite, support for Notes / reader / every
surface, options page with tunable weights, onboarding flow.

## Not in scope for this product

This is deliberately **not** a multi-user recommendation platform. The following
belong to a separate, server-based product — not a later version of this one:

- **Collaborative filtering** ("people who read X also read Y") across users
- Any **backend, accounts, or pooling of multiple users' histories**
- Server-side storage of behavioral data (which would bring consent, privacy-law,
  and data-handling obligations this extension avoids by design)

Keeping those out is what lets this ship as a small, private, single-purpose tool.
