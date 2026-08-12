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
  let SETTINGS = {
    rerank: true,
    sort: "recommended",
    autoRead: true,
    showHidden: false,
    weights: { like: 3, read: 1, notint: -3, hide: -5 },
  };
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
  const LABELS = { like: "Like", read: "Mark read", notint: "Not interesting", hide: "Hide" };

  function annotate(el, post, ranked) {
    const f = fbFor(post.id);
    el.dataset.paiaId = post.id;
    let bar = el.querySelector(":scope > .paia-bar");
    if (!bar) {
      bar = document.createElement("div");
      bar.className = "paia-bar";
      bar.setAttribute("role", "group");
      bar.setAttribute("aria-label", "Post feedback");
      bar.innerHTML =
        `<span class="paia-score" aria-hidden="true"></span>` +
        Object.keys(ICON)
          .map(
            (act) =>
              `<button class="paia-btn" type="button" data-act="${act}" title="${LABELS[act]}" aria-label="${LABELS[act]}" aria-pressed="false">${ICON[act]}</button>`
          )
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
      // Auto-read: opening a post (clicking the card, not our controls) marks it
      // read. Bound once; writes storage without a re-render so it doesn't
      // reshuffle the feed mid-navigation.
      el.addEventListener("click", (e) => {
        if (!SETTINGS.autoRead || e.target.closest(".paia-bar")) return;
        const cur = FEEDBACK[post.id] || { read: false, like: false, hide: false, notint: false };
        if (cur.read) return;
        cur.read = true;
        FEEDBACK[post.id] = cur;
        PaiaStore.setFeedback(FEEDBACK);
        const rb = bar.querySelector('.paia-btn[data-act="read"]');
        if (rb) rb.classList.add("on");
      });
      el.appendChild(bar);
    }
    const score = bar.querySelector(".paia-score");
    const why = ranked && ranked.reasons && ranked.reasons.length ? "Why this rank: " + ranked.reasons.join(" · ") : "";
    score.textContent = ranked ? ranked.score.toFixed(1) : "";
    score.title = why;
    bar.querySelectorAll("button").forEach((b) => {
      const on = !!f[b.dataset.act];
      b.classList.toggle("on", on);
      b.setAttribute("aria-pressed", String(on));
    });
    const hideBtn = bar.querySelector('.paia-btn[data-act="hide"]');
    if (hideBtn) {
      hideBtn.title = f.hide ? "Restore" : "Hide";
      hideBtn.setAttribute("aria-label", f.hide ? "Restore" : "Hide");
    }
    el.classList.toggle("paia-hidden", !!f.hide);
    // Collapse hidden cards out of view unless "show hidden" is on.
    el.classList.toggle("paia-collapsed", !!f.hide && !SETTINGS.showHidden);
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

  function restoreAllHidden() {
    let changed = false;
    Object.keys(FEEDBACK).forEach((id) => {
      if (FEEDBACK[id] && FEEDBACK[id].hide) {
        FEEDBACK[id].hide = false;
        changed = true;
      }
    });
    if (changed) {
      PaiaStore.setFeedback(FEEDBACK);
      render();
    }
  }

  function hiddenCount() {
    return Object.values(FEEDBACK).filter((f) => f && f.hide).length;
  }
  function signalCount() {
    return Object.values(FEEDBACK).filter((f) => f && (f.like || f.read || f.hide || f.notint)).length;
  }

  // ---------- Floating panel ----------
  function injectPanel(count) {
    let panel = document.getElementById(PANEL_ID);
    if (!panel) {
      panel = document.createElement("div");
      panel.id = PANEL_ID;
      panel.setAttribute("role", "region");
      panel.setAttribute("aria-label", "Daily Briefing pAIa controls");
      panel.innerHTML = `
        <div class="paia-head"><span class="paia-dot" aria-hidden="true"></span> Daily Briefing pAIa</div>
        <div class="paia-error" id="paia-error" role="alert"></div>
        <label class="paia-ctl"><span>Re-rank this feed</span><input type="checkbox" id="paia-rerank"></label>
        <label class="paia-ctl"><span>Sort</span>
          <select id="paia-sort">
            <option value="recommended">Recommended</option>
            <option value="none">Original order</option>
          </select>
        </label>
        <label class="paia-ctl"><span>Mark read on open</span><input type="checkbox" id="paia-autoread"></label>
        <div class="paia-hidden-row" id="paia-hidden-row"></div>
        <div class="paia-count"></div>
        <div class="paia-hint" id="paia-hint"></div>`;
      document.body.appendChild(panel);
      panel.querySelector("#paia-rerank").addEventListener("change", (e) => setSetting({ rerank: e.target.checked }));
      panel.querySelector("#paia-sort").addEventListener("change", (e) => setSetting({ sort: e.target.value }));
      panel.querySelector("#paia-autoread").addEventListener("change", (e) => setSetting({ autoRead: e.target.checked }));
      // Delegated handlers for the dynamic hidden-row links.
      panel.addEventListener("click", (e) => {
        const act = e.target && e.target.dataset ? e.target.dataset.paiaAction : null;
        if (!act) return;
        e.preventDefault();
        if (act === "restore-all") restoreAllHidden();
        else if (act === "toggle-hidden") setSetting({ showHidden: !SETTINGS.showHidden });
      });
    }
    panel.querySelector("#paia-rerank").checked = !!SETTINGS.rerank;
    panel.querySelector("#paia-sort").value = SETTINGS.sort || "recommended";
    panel.querySelector("#paia-autoread").checked = !!SETTINGS.autoRead;
    panel.querySelector(".paia-count").textContent = count + " posts ranked";

    const hidden = hiddenCount();
    const row = panel.querySelector("#paia-hidden-row");
    if (hidden > 0) {
      row.innerHTML =
        `<span>${hidden} hidden</span>` +
        `<span><a href="#" data-paia-action="toggle-hidden">${SETTINGS.showHidden ? "Hide" : "Show"}</a>` +
        ` · <a href="#" data-paia-action="restore-all">Restore all</a></span>`;
      row.style.display = "";
    } else {
      row.innerHTML = "";
      row.style.display = "none";
    }

    panel.querySelector("#paia-hint").textContent =
      signalCount() === 0 ? "Tip: like, hide, or mark posts to train your feed." : "";
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

      const ranked = PaiaEngine.rank(items.map((i) => i.post), FEEDBACK, SETTINGS.weights);
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

  function showStorageError() {
    const el = document.getElementById("paia-error");
    if (el) el.textContent = "⚠ Couldn't save — storage may be full. Feedback won't persist.";
  }

  function boot() {
    // Surface a notice if a write ever fails (e.g. storage quota exceeded).
    PaiaStore.onError(() => showStorageError());
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
