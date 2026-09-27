"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const ROOT = path.join(__dirname, "..");
const read = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");

// Build a jsdom page from an inbox-style feed, load the extension's real
// engine/store/content scripts into it, and let the content script boot.
function makeFeed(extraCards = "") {
  const card = (slug, pub, pubName, title, date) => `
    <a href="https://${pub}.substack.com/p/${slug}?utm_source=%2Finbox" class="reader2-inbox-post">
      <div class="reader2-post-head">
        <div class="pub-name"><span class="hoverLink">${pubName}</span></div>
        <div class="inbox-item-timestamp">${date}</div>
      </div>
      <div class="reader2-post-body">
        <div class="reader2-post-title">${title}</div>
        <div class="reader2-item-meta">2 min read</div>
      </div>
    </a>`;
  return `<!DOCTYPE html><html><body>
    <nav><a href="https://x.substack.com/p/about-nav">About</a></nav>
    <div class="reader-nav-center"><div class="reader2-inbox-list">
      ${card("post-one", "nationalparkjournal", "National Park Journal", "Five Great Park Books", "Jul 23")}
      ${card("post-two", "nationalparkjournal", "National Park Journal", "July Park Roundup", "Jul 21")}
      ${card("post-three", "climatehope", "Climate Hope", "Weekly Climate Wins", "Jul 26")}
      ${extraCards}
    </div></div>
  </body></html>`;
}

async function boot(html, url = "https://substack.com/inbox") {
  // A real https URL gives jsdom a non-opaque origin, so window.localStorage
  // works out of the box (chrome is undefined here, so the store uses it).
  const dom = new JSDOM(html, {
    url,
    pretendToBeVisual: true,
    runScripts: "outside-only", // window.eval executes in the page's global scope
  });
  const { window } = dom;

  // Run engine.js, store.js, content.js in the window context so their IIFEs
  // attach to the window and operate on this document.
  const runIn = (code) => window.eval(code);
  runIn(read("engine.js"));
  runIn(read("store.js"));
  runIn(read("content.js"));

  // let boot()'s async reload() settle
  await new Promise((r) => setTimeout(r, 30));
  return { window, dom };
}

test("injects a feedback bar on every real post, excluding nav", async () => {
  const { window } = await boot(makeFeed());
  const bars = window.document.querySelectorAll(".paia-bar");
  assert.equal(bars.length, 3, "one bar per post");
  assert.equal(window.document.querySelector("nav .paia-bar"), null, "nav link not annotated");
  assert.ok(window.document.getElementById("paia-panel"), "floating panel present");
});

test("scrapes clean titles, publications and dates from inbox markup", async () => {
  const { window } = await boot(makeFeed());
  const snap = JSON.parse(window.localStorage.getItem("paia.ext.snapshot"));
  const titles = snap.map((p) => p.title);
  assert.ok(titles.includes("Five Great Park Books"));
  const pubs = snap.map((p) => p.publication).sort();
  assert.deepEqual([...new Set(pubs)].sort(), ["climatehope", "nationalparkjournal"]);
  assert.ok(snap.every((p) => p.publishedAt)); // dates captured
});

test("liking a post writes feedback and marks the button pressed", async () => {
  const { window } = await boot(makeFeed());
  const card = [...window.document.querySelectorAll(".reader2-inbox-post")].find((c) =>
    c.querySelector(".reader2-post-title").textContent.includes("Climate Wins")
  );
  card.querySelector('.paia-btn[data-act="like"]').dispatchEvent(new window.Event("click", { bubbles: true }));
  await new Promise((r) => setTimeout(r, 20));
  const fb = JSON.parse(window.localStorage.getItem("paia.ext.feedback"));
  const likedIds = Object.keys(fb).filter((k) => fb[k].like);
  assert.equal(likedIds.length, 1);
  assert.ok(likedIds[0].includes("climatehope"));
});

test("does not double-inject when the feed re-renders (dedupe)", async () => {
  const { window } = await boot(makeFeed());
  const before = window.document.querySelectorAll(".paia-bar").length;
  // append a duplicate of an existing post (same slug) — should not add a bar
  const list = window.document.querySelector(".reader2-inbox-list");
  const dup = window.document.querySelector(".reader2-inbox-post").cloneNode(true);
  dup.querySelector(".paia-bar") && dup.querySelector(".paia-bar").remove();
  list.appendChild(dup);
  await new Promise((r) => setTimeout(r, 800)); // let the debounced observer run
  const cardsWithTwoBars = [...window.document.querySelectorAll(".reader2-inbox-post")].filter(
    (c) => c.querySelectorAll(":scope > .paia-bar").length > 1
  );
  assert.equal(cardsWithTwoBars.length, 0, "no card has two bars");
});

test("stays inert on a single post page even with recommended /p/ links", async () => {
  // A reading view: the article plus a "more from this author" list of posts.
  const recs = [1, 2, 3, 4]
    .map(
      (n) => `<a href="https://x.substack.com/p/recommended-${n}" class="reader2-inbox-post">
        <div class="reader2-post-title">Recommended Post ${n}</div></a>`
    )
    .join("");
  const html = `<!DOCTYPE html><html><body>
    <article><h1>The Limits of Lake Victoria</h1><p>Long article body...</p></article>
    <div class="reader-nav-center"><div class="reader2-inbox-list">${recs}</div></div>
  </body></html>`;
  const { window } = await boot(html, "https://x.substack.com/p/the-limits-of-lake-victoria");
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0, "no bars while reading a post");
  assert.equal(window.document.getElementById("paia-panel"), null, "no panel while reading a post");
});

test("stays inert on the reader's single-post URL (/inbox/post/<id>)", async () => {
  const recs = [1, 2, 3, 4]
    .map(
      (n) => `<a href="https://x.substack.com/p/rec-${n}" class="reader2-inbox-post">
        <div class="reader2-post-title">Rec ${n}</div></a>`
    )
    .join("");
  const html = `<!DOCTYPE html><html><body>
    <article><h1>Solar Solves Everything</h1><p>Body...</p></article>
    <div class="reader-nav-center"><div class="reader2-inbox-list">${recs}</div></div>
  </body></html>`;
  const { window } = await boot(html, "https://substack.com/inbox/post/171234567");
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0, "no bars in reader post view");
  assert.equal(window.document.getElementById("paia-panel"), null);
});

test("activates on a publication archive feed (/archive)", async () => {
  const { window } = await boot(makeFeed(), "https://nationalparkjournal.substack.com/archive");
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 3, "bars on the archive feed");
  assert.ok(window.document.getElementById("paia-panel"), "panel on the archive feed");
});

test("stays inert on a publication post page even with an article-shaped path", async () => {
  const recs = [1, 2, 3, 4]
    .map(
      (n) => `<a href="https://x.substack.com/p/rec-${n}" class="reader2-inbox-post">
        <div class="reader2-post-title">Rec ${n}</div></a>`
    )
    .join("");
  const html = `<!DOCTYPE html><html><body>
    <div class="reader-nav-center"><div class="reader2-inbox-list">${recs}</div></div>
  </body></html>`;
  const { window } = await boot(html, "https://climatehope.substack.com/p/solar-solves-everything");
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0, "no bars on a post page");
});

test("stays inert while reading a post even at a feed URL (article-body /p/ links are not cards)", async () => {
  // The reader keeps the /inbox URL while showing an opened post. The article
  // body is full of embedded /p/ links, but none are preview cards.
  const html = `<!DOCTYPE html><html><body>
    <div class="reader-nav-center">
      <article>
        <h1>Solar Solves Everything</h1>
        <p>Read our earlier piece <a href="https://x.substack.com/p/solar-basics">on solar basics</a> for context.</p>
        <p>See also <a href="https://x.substack.com/p/battery-storage">battery storage</a> and <a href="https://x.substack.com/p/grid-reform">grid reform</a>.</p>
        <figure><a href="https://x.substack.com/p/solar-photo"><img alt="panels"></a><figcaption>Solar panels</figcaption></figure>
        <p>More: <a href="https://x.substack.com/p/heat-pumps">heat pumps</a>.</p>
      </article>
    </div>
  </body></html>`;
  const { window } = await boot(html, "https://substack.com/inbox");
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0, "no bars on article prose");
  assert.equal(window.document.getElementById("paia-panel"), null, "no panel while reading");
});

test("cleans up bars when navigating feed -> post via SPA (pushState)", async () => {
  const { window } = await boot(makeFeed()); // starts on /inbox -> bars
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 3, "bars on feed");
  // Simulate the reader's client-side navigation into a post.
  window.history.pushState({}, "", "/inbox/post/999");
  await new Promise((r) => setTimeout(r, 30));
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0, "bars removed after nav to post");
  assert.equal(window.document.getElementById("paia-panel"), null, "panel removed after nav to post");
});

test("stays inert on a non-feed page (too few posts)", async () => {
  const html = `<!DOCTYPE html><html><body><div class="reader-nav-center">
    <a href="https://x.substack.com/p/only-one" class="reader2-inbox-post">
      <div class="reader2-post-title">Solo Post</div></a>
  </div></body></html>`;
  const { window } = await boot(html);
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0);
  assert.equal(window.document.getElementById("paia-panel"), null);
});
