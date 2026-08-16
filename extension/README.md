# Daily Briefing pAIa — Chrome extension

A Manifest V3 Chrome extension that re-ranks your **Substack feed** based on your
own read / like / hide / not-interesting feedback. It's the "Option B" (in-page
re-ranker) version of the [Daily Briefing pAIa demo](../daily-briefing-paia-demo).

Everything runs locally — feedback and ranking stay in `chrome.storage.local`,
nothing is sent anywhere.

## What it does

On any Substack page it:
1. **Scrapes** the post cards in the feed (title, publication, author, date).
2. **Injects** a small feedback bar on each card — like ♥, mark read ✓, not
   interesting ⊘, hide ✕ — plus a live ranking score.
3. **Re-ranks** the cards in place using your accumulated feedback.
4. Shows a **floating panel** to toggle re-ranking, switch sort
   (Recommended / Original order), and toggle auto-read.

Click the toolbar icon for a **dashboard**: signal counts, publication affinity
bars, and your top-ranked posts.

### Also (v0.3)

- **Auto-read on open** — opening a post (clicking through) marks it read
  automatically; toggle it off with "Mark read on open".
- **"Why this rank?"** — hover a post's score to see the reasons behind it
  (e.g. "+6 nationalparkjournal · you liked this").
- **Hide / undo** — hidden posts collapse out of the feed. The panel shows
  "N hidden · Show · Restore all"; **Show** reveals them (dimmed) so you can
  un-hide individually.
- **First-run hint** in the panel until you've given any feedback.
- **Options page** (from the popup's "⚙ Options & weights" link) — enable
  re-rank, default sort, auto-read, show-hidden default, and **tunable signal
  weights** (like/read/not-interesting/hide) that flow into ranking live.

### Resilience & accessibility (v0.5)

- **Export / import** your signals as JSON, plus reset — from the options page.
- **Won't lose data** — a versioned storage schema with migration, and writes
  that fail (e.g. quota) surface a notice instead of breaking the feed.
- **Accessible** — labeled controls (`role`/`aria-label`/`aria-pressed`),
  keyboard focus outlines, and respect for `prefers-reduced-motion`.

## How ranking works

Each action carries a weight (like +3, read +1, not-interesting −3, hide −5).
Those roll up into per-**publication** and per-**author** affinity scores, and a
post's rank score is:

```
score = publicationAffinity + 0.6 × authorAffinity + freshness
        (+2 liked, −4 not-interesting, hidden sinks to the bottom)
```

The shared engine (`engine.js`) is identical across the content script, popup,
and service worker.

## Install (load unpacked)

1. Open `chrome://extensions`.
2. Turn on **Developer mode** (top right).
3. Click **Load unpacked** and select this `daily-briefing-extension/` folder.
4. Open any Substack feed (e.g. `substack.com/home`, `substack.com/inbox`, or a
   publication's archive). The feedback bars and floating panel appear.

## Files

| File | Role |
|------|------|
| `manifest.json` | MV3 manifest (permissions: `storage`; hosts: `*.substack.com`) |
| `engine.js` | Shared ranking engine (pure functions) |
| `store.js` | Storage adapter (`chrome.storage.local`, falls back to `localStorage`) |
| `content.js` | Scrape → inject → re-rank on the page |
| `content.css` | Styles for the injected UI |
| `background.js` | Service worker: defaults + toolbar badge |
| `popup.html/js/css` | Dashboard |
| `icons/` | Toolbar icons |
| `test/test-feed.html` | Mock Substack feed for verifying the pipeline in a plain browser |

## Testing without Substack

`test/test-feed.html` loads `engine.js`, `store.js`, and `content.js` against a
mock feed (storage falls back to `localStorage`), so you can verify scrape →
inject → re-rank without logging into Substack:

```sh
python3 -m http.server 4175
# open http://localhost:4175/test/test-feed.html          (simple mock)
# open http://localhost:4175/test/substack-archive.fixture.html  (real Substack markup)
```

`substack-archive.fixture.html` reproduces the real Substack archive DOM (hashed
class names, `data-testid="post-preview-title"`, `role="article"` cards,
`<time datetime>`, author links) captured from a live page, so it catches
selector regressions.

## Automated tests

Uses Node's built-in test runner (Node 18+). Only dev dependency is `jsdom` for
the DOM tests.

```sh
npm install   # installs jsdom
npm test      # 24 tests: engine + store + DOM/integration
npm run lint  # syntax check + "no remote code / eval" hardening check
```

- `tests/engine.test.js` — ranking engine: weights, affinity roll-up, scoring,
  freshness, ranking order, hidden-sinks, the no-lost-update case.
- `tests/store.test.js` — storage adapter: defaults + weight backfill, schema
  migration, export/import round-trip, and that a failed write returns `false`
  and fires `onError` instead of throwing.
- `tests/content.test.js` — loads the real `engine`/`store`/`content` scripts
  into a jsdom inbox feed: bar injection (nav excluded), scraping, liking →
  feedback, no double-injection on re-render, and staying inert on non-feed pages.

## How scraping works (v0.2)

Substack renders with **hashed/obfuscated class names**, so the scraper avoids
class-based selectors:

- A post is any `a[href*="/p/"]` that is **not** inside nav/header/footer/menu.
- The title link is preferred via `data-testid="post-preview-title"`, else any
  post link with title-length text.
- The **card** is the `role="article"` wrapper if present, else found by climbing
  from the title link until the parent would contain a *different* post (so the
  card's siblings are the other cards — needed for reordering).
- **Publication** comes from the post URL host (works for custom domains too);
  **author** from the byline profile link; **date** from `<time datetime>`.

Verified against a live archive (20 posts) and the fixture (5 posts, 2
publications, nav link correctly excluded).

## Supported surfaces (v0.2)

Two distinct Substack DOM structures are handled, each verified against a fixture
built from real captured markup:

- **Publication archive** (`pub.substack.com/archive`) — cards use
  `data-testid="post-preview-title"` and `role="article"`.
- **Reader inbox** (`substack.com/inbox`) — cards are `a.reader2-inbox-post`
  with `.reader2-post-title`, `.pub-name`, `.inbox-item-timestamp`. The whole
  feed sits inside a `reader-nav-center` container, so the nav filter matches
  only semantic landmarks (`<nav>`/`<header>`/`role="navigation"`), never
  "nav"-in-a-class.

## Known limitations (v0.2)

- **`/home` (root) is a Notes/activity feed**, not the reading list — sparse in
  article links and structurally different. The target reader feed is `/inbox`.
  A live logged-in pass on `/inbox` is still worth doing to confirm at scale.
- **Inbox freshness is inactive.** Inbox timestamps like "Jul 23" (no year) don't
  parse to a reliable date, so the freshness term is ~0 there; ranking still
  works via publication/author affinity. Parsing relative/short dates is a
  follow-up.
- **Custom-domain publications aren't matched.** The manifest matches
  `*.substack.com`, which covers `substack.com/inbox` and `/home` (where all
  subscriptions aggregate). Individual publications on custom domains (e.g.
  `astralcodexten.com`) would need broader host permissions.
- **Reordering fights SPA re-renders.** Re-ordering nodes via the DOM can be
  undone when Substack re-renders the list; the MutationObserver re-applies, but
  very dynamic pages may flicker.
- **Reads are explicit only.** No automatic read detection yet — mark reads with
  the ✓ button.

## Possible next steps

- Auto-detect reads from scroll depth / time on page.
- Category/tag affinity in addition to publication/author.
- Sync signals across devices via `chrome.storage.sync`.
- An "explain this ranking" tooltip on each card.
