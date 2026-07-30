/* Daily Briefing pAIa — content script.
 * Runs on Substack pages (and the test harness). It:
 *   1. scrapes post cards from the feed,
 *   2. injects a small feedback bar (like / read / not-interesting / hide) on each,
 *   3. re-ranks the cards in place using the shared engine,
 *   4. shows a floating control panel.
 * All feedback lives in storage; nothing leaves the browser.
 *
 * NOTE: Substack's markup changes over time. The selectors below are defensive
 * and derive the publication from the post URL's subdomain (a stable signal),
 * but the card detection may need tuning against the live DOM.
 */
(function () {
  "use strict";

  const PANEL_ID = "paia-panel";
  let SETTINGS = { rerank: true, sort: "recommended" };
  let FEEDBACK = {};
  let mutating = false; // guards our own DOM writes from the MutationObserver
  let origCounter = 0; // assigns each card its original document-order index

  // ---------- Scraping ----------
  // Substack ships hashed/obfuscated class names and deeply nested cards, so we
  // avoid class-based selectors. A post is identified by its /p/<slug> link; the
  // card is found by climbing until the parent would contain a *different* post.
  const POST_RE = /\/p\/[^/]+/;

  // Normalize any post URL (including /p/slug/comments, query params) to its
  // canonical origin + /p/<slug> so links to the same post dedupe.
  function postPath(href) {
    try {
      const u = new URL(href);
      const m = u.pathname.match(/^(.*\/p\/[^/]+)/);
      return m ? u.origin + m[1] : null;
    } catch {
      return null;
    }
  }
  function isPostAnchor(a) {
    try {
      return POST_RE.test(new URL(a.href).pathname);
    } catch {
      return false;
    }
  }
  // Exclude nav / header / footer chrome (which also link to /p/ pages). Match
  // only semantic landmarks — NOT utility/hashed classes, because Substack uses
  // "nav" in layout class names (e.g. "reader-nav-center", the feed column).
  // Short-text links (icons, menu items) are filtered separately by title length.
  function inChrome(el) {
    return !!el.closest('nav, header, footer, [role="navigation"], [role="banner"], [role="contentinfo"]');
  }
  function distinctPostPaths(el) {
    const s = new Set();
    el.querySelectorAll('a[href*="/p/"]').forEach((a) => {
      if (isPostAnchor(a)) {
        const p = postPath(a.href);
        if (p) s.add(p);
      }
    });
    return s;
  }
  function pubFromHref(href) {
    try {
      const h = new URL(href).hostname;
      if (h.endsWith(".substack.com")) return h.replace(".substack.com", "");
      return h.replace(/^www\./, "");
    } catch {
      return "";
    }
  }

  function pickTitle(card, a) {
    // Prefer explicit title elements; fall back to the anchor text. On the inbox
    // the anchor wraps the whole card, so its raw text is a concatenated mess —
    // the .reader2-post-title lookup avoids that.
    const el = card.querySelector(
      '[data-testid="post-preview-title"], .reader2-post-title, [class*="post-title" i], h1, h2, h3'
    );
    const t = (el && el.textContent.trim()) || a.textContent.trim();
    return t.slice(0, 200);
  }
  function pickAuthor(card) {
    // Prefer an author/profile link; fall back to the name after the date separator.
    const link = card.querySelector('a[href*="/@"], a[href*="/people/"]');
    if (link && link.textContent.trim()) return link.textContent.trim().slice(0, 80);
    const m = card.textContent
      .replace(/\s+/g, " ")
      .match(/(?:ago|AM|PM|20\d\d)\s*[•·|]\s*([A-Za-z][^•·|\d]{1,38})/);
    return m ? m[1].trim() : "";
  }
  function pickDate(card) {
    const t = card.querySelector("time");
    if (t) return t.getAttribute("datetime") || t.textContent.trim();
    // Inbox has no <time>; the timestamp is a plain element (e.g. "Jul 23").
    const ts = card.querySelector('.inbox-item-timestamp, [class*="timestamp" i]');
    return ts ? ts.textContent.trim() : "";
  }
  function pickMinutes(card) {
    const m = card.textContent.match(/(\d+)\s*min/);
    return m ? Number(m[1]) : null;
  }

  function scrape() {
    // 1. Candidate title anchors: real post links, outside nav. Substack marks
    //    the title link with data-testid="post-preview-title"; otherwise we
    //    require title-length text to skip icon/thumbnail links.
    const titleAnchors = [];
    const seen = new Set();
    document.querySelectorAll('a[href*="/p/"]').forEach((a) => {
      if (!isPostAnchor(a) || inChrome(a)) return;
      const isTitle =
        a.dataset.testid === "post-preview-title" ||
        a.classList.contains("reader2-inbox-post") || // inbox: the card is the anchor
        a.textContent.trim().length > 10;
      if (!isTitle) return;
      const id = postPath(a.href);
      if (!id || seen.has(id)) return;
      seen.add(id);
      titleAnchors.push({ a, id });
    });

    // 2. Card container: prefer the semantic role="article" wrapper Substack uses;
    //    otherwise climb until the parent would contain a *different* post (its
    //    parent then holds the sibling cards, which we need for reordering).
    const items = [];
    for (const { a, id } of titleAnchors) {
      let card = a.closest('[role="article"]');
      if (!card) {
        card = a;
        while (card.parentElement && card.parentElement !== document.body) {
          if (distinctPostPaths(card.parentElement).size > 1) break;
          card = card.parentElement;
        }
      }
      const pub = pubFromHref(id);
      items.push({
        el: card,
        post: {
          id,
          url: id,
          title: pickTitle(card, a),
          publication: pub,
          author: pickAuthor(card) || pub,
          publishedAt: pickDate(card),
          minutes: pickMinutes(card),
        },
      });
    }
    return items;
  }

  // ---------- Feedback ----------
  function fbFor(id) {
    return FEEDBACK[id] || { read: false, like: false, hide: false, notint: false };
  }
  // Mutate the in-memory FEEDBACK synchronously (single-threaded, so no
  // interleaving), then persist and re-render. Re-reading storage here instead
  // would risk a lost update when two clicks land before the first write flushes.
  function toggle(id, act) {
    const f = FEEDBACK[id] || { read: false, like: false, hide: false, notint: false };
    f[act] = !f[act];
    FEEDBACK[id] = f;
    PaiaStore.setFeedback(FEEDBACK);
    render();
  }

  // ---------- Injection ----------
  const ICON = { like: "♥", read: "✓", notint: "⊘", hide: "✕" };

  function annotate(el, post, ranked) {
    const f = fbFor(post.id);
    let bar = el.querySelector(":scope > .paia-bar");
    if (!bar) {
      bar = document.createElement("div");
      bar.className = "paia-bar";
      bar.innerHTML =
        `<span class="paia-score"></span>` +
        Object.keys(ICON)
          .map((act) => `<button class="paia-btn" data-act="${act}" title="${act}">${ICON[act]}</button>`)
          .join("");
      bar.querySelectorAll("button").forEach((b) =>
        b.addEventListener("click", (e) => {
          e.preventDefault();
          e.stopPropagation();
          toggle(post.id, b.dataset.act);
        })
      );
      if (getComputedStyle(el).position === "static") el.style.position = "relative";
      // Capture original document order once, so "Original order" can restore it
      // even after we've reshuffled the DOM.
      if (!el.dataset.paiaOrig) el.dataset.paiaOrig = String(origCounter++);
      el.appendChild(bar);
    }
    bar.querySelector(".paia-score").textContent = ranked ? ranked.score.toFixed(1) : "";
    bar.querySelectorAll("button").forEach((b) => b.classList.toggle("on", !!f[b.dataset.act]));
    el.classList.toggle("paia-hidden", !!f.hide);
  }

  // Reorder cards within their shared parent. By score when re-ranking is on,
  // otherwise back to the captured original document order.
  function applyOrder(items, scoreById) {
    const groups = new Map();
    items.forEach((i) => {
      const p = i.el.parentElement;
      if (!p) return;
      if (!groups.has(p)) groups.set(p, []);
      groups.get(p).push(i);
    });
    let best = null;
    groups.forEach((arr, p) => {
      if (!best || arr.length > best.arr.length) best = { p, arr };
    });
    if (!best || best.arr.length < 3) return;

    const byScore = SETTINGS.rerank && SETTINGS.sort === "recommended";
    const sorted = best.arr.slice().sort((a, b) =>
      byScore
        ? scoreById.get(b.post.id).score - scoreById.get(a.post.id).score
        : Number(a.el.dataset.paiaOrig) - Number(b.el.dataset.paiaOrig)
    );
    sorted.forEach((i) => best.p.appendChild(i.el)); // appendChild moves nodes in order
  }

  // ---------- Floating panel ----------
  function injectPanel(count) {
    let panel = document.getElementById(PANEL_ID);
    if (!panel) {
      panel = document.createElement("div");
      panel.id = PANEL_ID;
      panel.innerHTML = `
        <div class="paia-head"><span class="paia-dot"></span> Daily Briefing pAIa</div>
        <label class="paia-ctl"><input type="checkbox" id="paia-rerank"> Re-rank this feed</label>
        <label class="paia-ctl">Sort
          <select id="paia-sort">
            <option value="recommended">Recommended</option>
            <option value="none">Original order</option>
          </select>
        </label>
        <div class="paia-count"></div>`;
      document.body.appendChild(panel);
      panel.querySelector("#paia-rerank").addEventListener("change", (e) => setSetting({ rerank: e.target.checked }));
      panel.querySelector("#paia-sort").addEventListener("change", (e) => setSetting({ sort: e.target.value }));
    }
    panel.querySelector("#paia-rerank").checked = !!SETTINGS.rerank;
    panel.querySelector("#paia-sort").value = SETTINGS.sort || "recommended";
    panel.querySelector(".paia-count").textContent = count + " posts ranked";
  }

  // ---------- Main ----------
  // render() works from the in-memory FEEDBACK/SETTINGS (no storage read), so
  // it's safe to call synchronously right after a local mutation.
  const MIN_POSTS = 3; // stay inert on non-feed pages (single post, about, etc.)

  function render() {
    const items = scrape();
    if (items.length < MIN_POSTS) return;

    mutating = true;
    try {
      PaiaStore.setSnapshot(items.map((i) => i.post)); // for the popup dashboard

      const ranked = PaiaEngine.rank(items.map((i) => i.post), FEEDBACK);
      const scoreById = new Map(ranked.map((r) => [r.post.id, r]));

      items.forEach(({ el, post }) => annotate(el, post, scoreById.get(post.id)));
      applyOrder(items, scoreById);
      injectPanel(items.length);
    } finally {
      // release the guard after the current mutation batch settles
      setTimeout(() => (mutating = false), 0);
    }
  }

  // reload() pulls the latest state from storage, then renders. Used on boot and
  // when another surface (the popup) changes storage.
  async function reload() {
    SETTINGS = await PaiaStore.getSettings();
    FEEDBACK = await PaiaStore.getFeedback();
    render();
  }

  async function setSetting(patch) {
    SETTINGS = Object.assign({}, SETTINGS, patch);
    await PaiaStore.setSettings(SETTINGS);
    render();
  }

  function debounce(fn, ms) {
    let t;
    return () => {
      clearTimeout(t);
      t = setTimeout(fn, ms);
    };
  }

  function boot() {
    reload();
    // Re-render on infinite scroll / feed updates (uses in-memory state).
    const scheduled = debounce(() => {
      if (!mutating) render();
    }, 700);
    new MutationObserver(() => {
      if (!mutating) scheduled();
    }).observe(document.body, { childList: true, subtree: true });
    // Pick up changes made in the popup (e.g. reset, settings).
    PaiaStore.onChange(() => reload());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
