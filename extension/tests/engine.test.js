"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { PaiaEngine } = require("../engine.js");

// Small helpers
const post = (id, publication, author, publishedAt) => ({
  id,
  url: id,
  title: id,
  publication,
  author: author || publication,
  publishedAt: publishedAt || "",
});
const liked = { read: false, like: true, hide: false, notint: false };
const readOnly = { read: true, like: false, hide: false, notint: false };
const notint = { read: false, like: false, hide: false, notint: true };
const hidden = { read: false, like: false, hide: true, notint: false };

test("weightOf sums active signals with default weights", () => {
  assert.equal(PaiaEngine.weightOf(liked), 3);
  assert.equal(PaiaEngine.weightOf(readOnly), 1);
  assert.equal(PaiaEngine.weightOf(notint), -3);
  assert.equal(PaiaEngine.weightOf(hidden), -5);
  assert.equal(PaiaEngine.weightOf({ read: true, like: true, hide: false, notint: false }), 4);
  assert.equal(PaiaEngine.weightOf(undefined), 0);
});

test("weightOf honors custom weights", () => {
  const w = { like: 10, read: 2, notint: -1, hide: -20 };
  assert.equal(PaiaEngine.weightOf(liked, w), 10);
  assert.equal(PaiaEngine.weightOf(hidden, w), -20);
});

test("buildAffinities aggregates per publication and author", () => {
  const posts = [post("a", "platformer", "Casey"), post("b", "platformer", "Casey"), post("c", "lenny", "Lenny")];
  const fb = { a: liked, b: liked, c: notint };
  const aff = PaiaEngine.buildAffinities(posts, fb);
  assert.equal(aff.pub.platformer, 6); // two likes
  assert.equal(aff.pub.lenny, -3); // one not-interesting
  assert.equal(aff.author.Casey, 6);
  assert.equal(aff.author.Lenny, -3);
});

test("buildAffinities uses custom weights", () => {
  const posts = [post("a", "platformer", "Casey")];
  const aff = PaiaEngine.buildAffinities(posts, { a: liked }, { like: 100, read: 1, notint: -3, hide: -5 });
  assert.equal(aff.pub.platformer, 100);
});

test("rank sorts liked publications to the top", () => {
  const posts = [
    post("a", "platformer", "Casey"),
    post("b", "lenny", "Lenny"),
    post("c", "platformer", "Casey"),
  ];
  const fb = { a: liked }; // like one platformer post
  const ranked = PaiaEngine.rank(posts, fb);
  // both platformer posts should outrank the lenny post
  const order = ranked.map((r) => r.post.id);
  assert.ok(order.indexOf("a") < order.indexOf("b"));
  assert.ok(order.indexOf("c") < order.indexOf("b"));
});

test("hidden posts sink to the bottom", () => {
  const posts = [post("a", "x"), post("b", "y"), post("c", "z")];
  const ranked = PaiaEngine.rank(posts, { a: hidden });
  assert.equal(ranked[ranked.length - 1].post.id, "a");
  assert.ok(ranked[ranked.length - 1].score <= -90); // large penalty
});

test("liked post gets the +2 direct bonus on top of affinity", () => {
  const posts = [post("a", "x", "X")];
  const ranked = PaiaEngine.rank(posts, { a: liked });
  // pub 3 + author 3*0.6 + like 2 = 6.8 (freshness 0, no date)
  assert.ok(Math.abs(ranked[0].score - 6.8) < 1e-9, `got ${ranked[0].score}`);
});

test("not-interesting applies a -4 direct penalty", () => {
  const posts = [post("a", "x", "X")];
  const ranked = PaiaEngine.rank(posts, { a: notint });
  // pub -3 + author -3*0.6 + notint -4 = -8.8
  assert.ok(Math.abs(ranked[0].score - -8.8) < 1e-9, `got ${ranked[0].score}`);
});

test("scorePost emits human-readable reasons", () => {
  const posts = [post("a", "platformer", "Casey")];
  const aff = PaiaEngine.buildAffinities(posts, { a: liked });
  const { reasons } = PaiaEngine.scorePost(posts[0], aff, { a: liked });
  assert.ok(reasons.some((r) => r.includes("platformer")));
  assert.ok(reasons.some((r) => r.includes("Casey")));
  assert.ok(reasons.some((r) => r.toLowerCase().includes("liked")));
});

test("baseline post reports 'baseline + freshness'", () => {
  const posts = [post("a", "x", "X")];
  const aff = PaiaEngine.buildAffinities(posts, {});
  const { reasons } = PaiaEngine.scorePost(posts[0], aff, {});
  assert.deepEqual(reasons, ["baseline + freshness"]);
});

test("freshness decays with age and is never negative", () => {
  const now = new Date().toISOString();
  const old = new Date(Date.now() - 60 * 86400000).toISOString();
  assert.ok(PaiaEngine.freshness(now) > PaiaEngine.freshness(old));
  assert.equal(PaiaEngine.freshness(old), 0); // 60 days -> clamped to 0
  assert.equal(PaiaEngine.freshness(""), 0); // unparseable
  assert.equal(PaiaEngine.freshness("not a date"), 0);
});

test("no lost update: two independent likes both count in affinity", () => {
  // Mirrors the race we fixed in the content script: distinct posts both liked.
  const posts = [post("a", "platformer"), post("b", "platformer")];
  const fb = { a: liked, b: liked };
  const aff = PaiaEngine.buildAffinities(posts, fb);
  assert.equal(aff.pub.platformer, 6);
});
