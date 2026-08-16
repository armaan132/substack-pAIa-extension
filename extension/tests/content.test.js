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

async function boot(html) {
  // A real https URL gives jsdom a non-opaque origin, so window.localStorage
  // works out of the box (chrome is undefined here, so the store uses it).
  const dom = new JSDOM(html, {
    url: "https://substack.com/inbox",
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

test("stays inert on a non-feed page (too few posts)", async () => {
  const html = `<!DOCTYPE html><html><body><div class="reader-nav-center">
    <a href="https://x.substack.com/p/only-one" class="reader2-inbox-post">
      <div class="reader2-post-title">Solo Post</div></a>
  </div></body></html>`;
  const { window } = await boot(html);
  assert.equal(window.document.querySelectorAll(".paia-bar").length, 0);
  assert.equal(window.document.getElementById("paia-panel"), null);
});
