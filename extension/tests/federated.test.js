"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { PaiaFederated } = require("../federated.js");
const { PaiaTopic } = require("../topic.js");
const { PaiaEngine } = require("../engine.js");

const like = { read: false, like: true, hide: false, notint: false };
const weightOf = (f) => PaiaEngine.weightOf(f, PaiaEngine.WEIGHTS);

// Build a client's shareable update from its own posts + feedback.
function clientUpdate(posts, feedback) {
  const model = PaiaTopic.buildModel(posts, feedback, weightOf);
  return PaiaFederated.toUpdate(model, model.rated);
}

test("toUpdate exposes only term weights + a sample count (no raw data)", () => {
  const posts = [{ id: "a", title: "Quantum error correction" }];
  const model = PaiaTopic.buildModel(posts, { a: like }, weightOf);
  const update = PaiaFederated.toUpdate(model, model.rated);
  assert.deepEqual(Object.keys(update).sort(), ["samples", "termAff"]);
  assert.equal(update.samples, 1);
  // Privacy: the update must not carry feedback, ids, or titles.
  const json = JSON.stringify(update);
  assert.ok(!/quantum error correction/i.test(json), "no raw titles leak");
  assert.ok(!/\bid\b|feedback|\blike\b/i.test(json), "no feedback/ids leak");
  assert.ok(update.termAff.quantum > 0, "but the learned weight is present");
});

test("toUpdate copies weights so later local training can't mutate a sent update", () => {
  const model = PaiaTopic.buildModel([{ id: "a", title: "quantum physics" }], { a: like }, weightOf);
  const update = PaiaFederated.toUpdate(model, model.rated);
  model.termAff.quantum = 999; // simulate more local training after sending
  assert.notEqual(update.termAff.quantum, 999, "sent update is isolated");
});

test("aggregate is a sample-weighted mean (FedAvg)", () => {
  // Two clients, one term. Client A: weight 1.0, 3 samples. Client B: weight 3.0, 1 sample.
  // Expected global = (3*1.0 + 1*3.0) / (3+1) = 6/4 = 1.5
  const global = PaiaFederated.aggregate([
    { termAff: { x: 1.0 }, samples: 3 },
    { termAff: { x: 3.0 }, samples: 1 },
  ]);
  assert.ok(Math.abs(global.termAff.x - 1.5) < 1e-9, "weighted average");
  assert.equal(global.clients, 2);
});

test("aggregate falls back to equal weights when no samples reported", () => {
  const global = PaiaFederated.aggregate([
    { termAff: { x: 2 }, samples: 0 },
    { termAff: { x: 4 }, samples: 0 },
  ]);
  assert.ok(Math.abs(global.termAff.x - 3) < 1e-9); // (2+4)/2
});

test("aggregate handles empty input safely", () => {
  const global = PaiaFederated.aggregate([]);
  assert.equal(Object.keys(global.termAff).length, 0);
  assert.equal(global.clients, 0);
});

test("federated round transfers knowledge between clients without sharing data", () => {
  // Client A only ever engages with quantum posts; client B only with climate.
  const aPosts = [
    { id: "a1", title: "Quantum computing milestone" },
    { id: "a2", title: "Quantum error correction" },
  ];
  const bPosts = [
    { id: "b1", title: "Climate policy shift" },
    { id: "b2", title: "Climate adaptation funding" },
  ];
  const updateA = clientUpdate(aPosts, { a1: like, a2: like });
  const updateB = clientUpdate(bPosts, { b1: like, b2: like });

  // Coordinator sees only the two weight vectors — never A's or B's feedback.
  const global = PaiaFederated.round([updateA, updateB]);

  // A fresh post on each topic, scored against the GLOBAL model.
  const quantumPost = { id: "q", title: "A quantum networking advance" };
  const climatePost = { id: "c", title: "New climate modelling" };
  const sQuantum = PaiaTopic.score(quantumPost, global).score;
  const sClimate = PaiaTopic.score(climatePost, global).score;

  // Both topics are now known globally: client B (never saw quantum) would get
  // quantum recommended, and A would get climate — knowledge crossed over via
  // shared weights alone.
  assert.ok(sQuantum > 0, "global model learned quantum from client A");
  assert.ok(sClimate > 0, "global model learned climate from client B");
});

test("a client's global score beats its local-only score for an unseen topic", () => {
  // Client B has only climate feedback; locally it knows nothing about quantum.
  const bPosts = [{ id: "b1", title: "Climate policy shift" }];
  const bLocal = PaiaTopic.buildModel(bPosts, { b1: like }, weightOf);
  const quantumPost = { id: "q", title: "Quantum computing milestone" };
  assert.equal(PaiaTopic.score(quantumPost, bLocal).score, 0, "locally, quantum is unknown");

  // After a federated round with a quantum-loving client A, B's global model knows it.
  const aPosts = [{ id: "a1", title: "Quantum computing milestone" }];
  const updateA = PaiaFederated.toUpdate(
    PaiaTopic.buildModel(aPosts, { a1: like }, weightOf),
    1
  );
  const updateB = PaiaFederated.toUpdate(bLocal, bLocal.rated);
  const global = PaiaFederated.round([updateA, updateB]);
  assert.ok(PaiaTopic.score(quantumPost, global).score > 0, "federation taught B about quantum");
});
