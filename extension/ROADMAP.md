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

- ✅ Map the live DOM against a real Substack page — found hashed class names,
  `data-testid="post-preview-title"`, and `role="article"` cards
- ✅ Harden `scrape()` / `pickTitle` / `pickAuthor` / `pickDate` — now
  class-independent; verified extracting 20 posts on a live archive
- ✅ Solid card-container detection (`role="article"` + climb fallback); nav /
  header links correctly excluded
- ✅ Dedupe by canonical `/p/<slug>` (comment links collapse into the post)
- ✅ Inert on non-feed pages (`MIN_POSTS` threshold)
- ✅ Save a real-markup fixture (`test/substack-archive.fixture.html`)
- ✅ Publication archive page supported (validated against Astral Codex Ten)
- ✅ Infinite-scroll dedup verified — simulated "load more": new post gets a bar,
  zero duplicate bars on existing cards, duplicate-slug cards deduped
- ✅ **Inbox support added** — inspected the real logged-in `/inbox` DOM, found it
  differs from the archive (`a.reader2-inbox-post`, `.reader2-post-title`,
  `.inbox-item-timestamp`, feed wrapped in `reader-nav-center`); fixed the nav
  filter false-positive and added inbox selectors; verified against a fixture
  built from captured markup (titles, dates, publications, reorder all correct)
- ✅ **Live logged-in `/inbox` pass at scale** — confirmed on a real feed:
  **140 posts** detected with correct titles, publications, and dates

**Testing gate:** bars appear, re-rank works, zero duplicate bars, nav excluded,
no console errors — ✅ met against mock, archive fixture, inbox fixture, AND the
live logged-in `/inbox` (140 posts).

**Exit:** ✅ works on a real Substack feed without hand-editing selectors — met
for both the archive and the logged-in inbox. **Week 1 complete.**

---

## Week 2 — Core features (v0.3–0.4)

Make it genuinely useful, not just a demo.

- ✅ **Auto-read detection** — marks a post read when you open it (click-through),
  the strongest signal on a feed; toggleable via "Mark read on open". (Scroll/
  dwell was the original idea but click-through fits a feed better.)
- ✅ **"Why this rank?"** tooltip — hover the score to see the reasons the engine
  used (e.g. "+6 nationalparkjournal · you liked this")
- ✅ **Undo hide** — hidden posts collapse out of the feed; panel shows
  "N hidden · Show · Restore all", and Show reveals them (dimmed) to un-hide
- ✅ **First-run hint** in the panel; the popup already has empty states
- ✅ **Options page** (stretch, done) — a full settings page: enable re-rank,
  default sort, auto-read, show-hidden default, **tunable signal weights**
  (like/read/not-interesting/hide) with reset-to-defaults, and reset-all-data.
  Weights flow into ranking live (verified: Like=10 → liked post scores 18.0 vs
  6.8 at the default 3). Reachable from the popup's "⚙ Options & weights" link.
- ⭑ **Category/tag affinity** in addition to publication + author — deferred
  (Substack feed cards don't expose tags; would require keyword heuristics)

**Testing gate:** ✅ each feature verified against the inbox fixture (tooltip,
auto-read on click, hide→collapse→show→restore-all, first-run hint), and
archive + mock still pass — no regressions.

**Exit:** ✅ usable day to day — met.

---

## Week 3 — Resilience & accessibility (v0.5)

- ✅ **Storage schema version + migration** — a `schema` key with an idempotent
  `migrate()`; `getSettings` back-fills missing keys (e.g. weights) so older
  data upgrades cleanly instead of being wiped
- ✅ **Quota / write-failure handling** — `set()` never throws; a failed save
  returns `false` and surfaces "⚠ Couldn't save — storage may be full" in the
  panel instead of breaking the feed
- ✅ **Export / import signals (JSON)** — from the options page, with a confirmed
  "Reset all feedback"
- ✅ **Accessibility** — feedback bar is a labeled `role="group"`; buttons are
  real `<button type="button">` with `aria-label` + `aria-pressed`; panel is a
  labeled `role="region"`; error is a `role="alert"`; keyboard `:focus-visible`
  outlines; `prefers-reduced-motion` disables transitions
- ◻️ Visual QA in Substack light **and** dark themes — the injected UI is dark,
  high-contrast, and readable on both; a formal pass on a live light-theme feed
  is still worth doing
- ⭑ `chrome.storage.sync` option with a local fallback — deferred

**Testing gate:** ✅ migration sets schema v1 and back-fills weights; export
round-trips and import restores feedback+settings; write-failure shows the notice
and returns false; ARIA roles/labels/aria-pressed verified; no regressions.

**Exit:** ✅ no data-loss paths; controls are keyboard- and screen-reader-operable.

---

## Week 4 — Testing & hardening (v0.9)

The QA week. Automate what's cheap; manually verify the rest. Uses Node's
built-in test runner (no framework); `jsdom` is the only dev dependency.

- ✅ **Unit tests** for `engine.js` (12) — weights (default + custom), affinity
  roll-up, scoring, freshness decay/clamping, ranking order, hidden-sinks,
  reasons, and the no-lost-update case
- ✅ **DOM/integration tests** for `content.js` (5, jsdom) — loads the real
  engine/store/content into an inbox feed: bar injection with nav excluded,
  scraping (titles/pubs/dates), liking → feedback, no double-injection on
  re-render, and inert on non-feed pages
- ✅ **Store tests** (7) — defaults + weight backfill, schema migration,
  export/import round-trip, and failed-write returns false + fires onError
- ✅ **Lint** — `npm run lint`: JS syntax check + a "no remote code / eval"
  scanner over shipped files
- ✅ **No remote code / CSP** — scanner passes; explicit MV3
  `content_security_policy` (`script-src 'self'`) added (hard Web Store rule)
- ✅ **Robustness** — degrades quietly on selector miss (inert), writes never
  throw; verified by tests
- ◻️ Formal perf/heap pass over a long live scroll — dedupe + debounce +
  mutating-guard verified; a heap snapshot on a real 5-min session still worth it
- ⭑ Playwright E2E loading the unpacked extension — deferred (jsdom integration
  + browser-fixture checks cover the loop)

**Testing gate:** ✅ `npm test` → **24/24 green**; `npm run lint` clean.

**Exit:** ✅ automated suite green; no-remote-code confirmed. Week 4 complete.

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
