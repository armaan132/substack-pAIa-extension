"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");
const { createCoordinator } = require("../server/coordinator.js");
const FLClient = require("../fl-client.js");
const { PaiaTopic } = require("../topic.js");
const { PaiaFederated } = require("../federated.js");
const { PaiaEngine } = require("../engine.js");

const like = { read: false, like: true, hide: false, notint: false };
const weightOf = (f) => PaiaEngine.weightOf(f, PaiaEngine.WEIGHTS);

function localUpdate(titles) {
  const posts = titles.map((t, i) => ({ id: "p" + i, title: t }));
  const feedback = Object.fromEntries(posts.map((p) => [p.id, like]));
  const model = PaiaTopic.buildModel(posts, feedback, weightOf);
  return PaiaFederated.toUpdate(model, model.rated);
}

// Spin up a coordinator on an ephemeral loopback port for one test, then close.
async function withCoordinator(fn) {
  const coord = createCoordinator();
  const addr = await coord.listen(0, "127.0.0.1");
  const baseUrl = `http://127.0.0.1:${addr.port}`;
  try {
    return await fn(baseUrl, coord);
  } finally {
    await coord.close();
  }
}

test("health endpoint reports an empty coordinator", async () => {
  await withCoordinator(async (baseUrl) => {
    const res = await fetch(baseUrl + "/health");
    const body = await res.json();
    assert.equal(res.status, 200);
    assert.equal(body.ok, true);
    assert.equal(body.clients, 0);
  });
});

test("clients submit weights over HTTP and the global model averages them", async () => {
  await withCoordinator(async (baseUrl) => {
    const ack = await FLClient.submitUpdate(baseUrl, "ava", localUpdate(["Quantum computing milestone"]));
    assert.equal(ack.ok, true);
    assert.equal(ack.clients, 1);
    await FLClient.submitUpdate(baseUrl, "ben", localUpdate(["Climate policy shift"]));

    const global = await FLClient.fetchGlobalModel(baseUrl);
    assert.equal(global.clients, 2);
    assert.ok(global.termAff.quantum > 0 && global.termAff.climate > 0);
  });
});

test("end-to-end: networked federation transfers a topic between clients", async () => {
  await withCoordinator(async (baseUrl) => {
    // Ben only knows climate locally; quantum is unknown to him.
    const benLocalModel = (() => {
      const posts = [{ id: "b", title: "Climate policy shift" }];
      return PaiaTopic.buildModel(posts, { b: like }, weightOf);
    })();
    const quantumPost = { title: "A quantum computing result" };
    assert.equal(PaiaTopic.score(quantumPost, benLocalModel).score, 0, "Ben knows no quantum locally");

    // Ava (quantum) and Ben (climate) both submit; Ben syncs and pulls global.
    await FLClient.submitUpdate(baseUrl, "ava", localUpdate(["Quantum computing milestone", "Quantum error correction"]));
    const global = await FLClient.syncRound(baseUrl, "ben", PaiaFederated.toUpdate(benLocalModel, benLocalModel.rated));

    assert.ok(global.clients === 2, "both clients present in the round");
    assert.ok(
      PaiaTopic.score(quantumPost, global).score > 0,
      "after the network round, Ben's global model recommends quantum"
    );
  });
});

test("coordinator rejects malformed updates (400) and ignores them", async () => {
  await withCoordinator(async (baseUrl) => {
    const bad = await fetch(baseUrl + "/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ clientId: "x", termAff: { q: "not-a-number" }, samples: 1 }),
    });
    assert.equal(bad.status, 400);
    const noId = await fetch(baseUrl + "/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ termAff: { q: 1 } }),
    });
    assert.equal(noId.status, 400);
    // Nothing was stored.
    const global = await FLClient.fetchGlobalModel(baseUrl);
    assert.equal(global.clients, 0);
  });
});

test("a re-submitting client replaces its own contribution (latest wins)", async () => {
  await withCoordinator(async (baseUrl) => {
    await FLClient.submitUpdate(baseUrl, "ava", localUpdate(["Quantum milestone"]));
    await FLClient.submitUpdate(baseUrl, "ava", localUpdate(["Climate funding"])); // same client, new interests
    const global = await FLClient.fetchGlobalModel(baseUrl);
    assert.equal(global.clients, 1, "still one client");
    assert.ok(global.termAff.climate > 0, "latest update applied");
    assert.equal(global.termAff.quantum, undefined, "old update replaced");
  });
});
