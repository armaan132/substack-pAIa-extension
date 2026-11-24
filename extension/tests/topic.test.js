"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { PaiaTopic } = require("../topic.js");
const { PaiaEngine } = require("../engine.js");

const liked = { read: false, like: true, hide: false, notint: false };
const hidden = { read: false, like: false, hide: true, notint: false };
const weightOf = (f) => PaiaEngine.weightOf(f, PaiaEngine.WEIGHTS);

test("tokenize lowercases, drops stopwords and short words", () => {
  assert.deepEqual(PaiaTopic.tokenize("The Quantum Brain AND a Neuron"), ["quantum", "brain", "neuron"]);
  assert.deepEqual(PaiaTopic.tokenize(""), []);
  assert.deepEqual(PaiaTopic.tokenize(null), []);
});

test("buildModel learns positive affinity for liked topics", () => {
  const posts = [
    { id: "a", title: "Quantum computing breakthrough", publication: "p" },
    { id: "b", title: "Gardening tips for spring", publication: "q" },
  ];
  const model = PaiaTopic.buildModel(posts, { a: liked }, weightOf);
  assert.equal(model.N, 2);
  assert.ok(model.termAff.quantum > 0, "quantum should have positive affinity");
  assert.equal(model.termAff.gardening, undefined, "unrated terms get no affinity");
});

test("buildModel learns negative affinity for hidden topics", () => {
  const posts = [{ id: "a", title: "Celebrity gossip roundup", publication: "p" }];
  const model = PaiaTopic.buildModel(posts, { a: hidden }, weightOf);
  assert.ok(model.termAff.celebrity < 0);
  assert.ok(model.termAff.gossip < 0);
});

test("score generalizes to an unrated post sharing a liked topic", () => {
  const posts = [
    { id: "a", title: "Quantum computing breakthrough", publication: "p" },
    { id: "b", title: "A new quantum algorithm", publication: "q" }, // unrated, shares "quantum"
    { id: "c", title: "Best pizza recipes", publication: "r" },
  ];
  const model = PaiaTopic.buildModel(posts, { a: liked }, weightOf);
  const sB = PaiaTopic.score(posts[1], model);
  const sC = PaiaTopic.score(posts[2], model);
  assert.ok(sB.score > 0, "post sharing a liked topic scores positive");
  assert.equal(sC.score, 0, "unrelated post scores zero");
  assert.ok(sB.top.includes("quantum"), "reason surfaces the driving term");
});

test("score returns neutral for empty model or empty title", () => {
  assert.deepEqual(PaiaTopic.score({ title: "anything here" }, null), { score: 0, top: [] });
  const model = PaiaTopic.buildModel([], {}, weightOf);
  assert.deepEqual(PaiaTopic.score({ title: "" }, model), { score: 0, top: [] });
});

test("engine.rank folds in topic scores and boosts a topically-similar post", () => {
  const posts = [
    { id: "a", title: "Quantum computing breakthrough", publication: "p", author: "p", publishedAt: "" },
    { id: "b", title: "A new quantum algorithm", publication: "q", author: "q", publishedAt: "" },
    { id: "c", title: "Best pizza recipes", publication: "r", author: "r", publishedAt: "" },
  ];
  const fb = { a: liked };
  const model = PaiaTopic.buildModel(posts, fb, weightOf);
  const topicScores = new Map(posts.map((p) => [p.id, PaiaTopic.score(p, model)]));

  const withTopic = PaiaEngine.rank(posts, fb, PaiaEngine.WEIGHTS, topicScores);
  const bWith = withTopic.find((r) => r.post.id === "b").score;

  const without = PaiaEngine.rank(posts, fb, PaiaEngine.WEIGHTS);
  const bWithout = without.find((r) => r.post.id === "b").score;

  assert.ok(bWith > bWithout, "topic model lifts the quantum post b above its baseline");
  // b (topic match, no pub affinity) should outrank c (unrelated).
  const idxB = withTopic.findIndex((r) => r.post.id === "b");
  const idxC = withTopic.findIndex((r) => r.post.id === "c");
  assert.ok(idxB < idxC, "topically similar post ranks above the unrelated one");
});

test("engine.rank without topicScores is unchanged (backward compatible)", () => {
  const posts = [
    { id: "a", title: "x", publication: "p", author: "p", publishedAt: "" },
    { id: "b", title: "y", publication: "q", author: "q", publishedAt: "" },
  ];
  const fb = { a: liked };
  const r = PaiaEngine.rank(posts, fb, PaiaEngine.WEIGHTS);
  assert.equal(r[0].post.id, "a"); // liked publication still wins, no errors
});
