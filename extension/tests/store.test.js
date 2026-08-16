"use strict";
const test = require("node:test");
const assert = require("node:assert/strict");

// Provide a controllable localStorage BEFORE requiring store.js (it runs a
// migration on load). chrome is undefined in Node, so the adapter uses this.
const backing = new Map();
let throwOnSet = false;
global.localStorage = {
  getItem: (k) => (backing.has(k) ? backing.get(k) : null),
  setItem: (k, v) => {
    if (throwOnSet) throw new Error("QuotaExceededError");
    backing.set(k, String(v));
  },
  removeItem: (k) => backing.delete(k),
  clear: () => backing.clear(),
};

const { PaiaStore } = require("../store.js");

test("getSettings returns defaults and backfills weights", async () => {
  backing.clear();
  const s = await PaiaStore.getSettings();
  assert.equal(s.rerank, true);
  assert.equal(s.sort, "recommended");
  assert.equal(s.autoRead, true);
  assert.deepEqual(s.weights, { like: 3, read: 1, notint: -3, hide: -5 });
});

test("partial stored settings are merged with defaults (weights backfilled)", async () => {
  backing.clear();
  await PaiaStore.setSettings({ rerank: false, weights: { like: 9 } });
  const s = await PaiaStore.getSettings();
  assert.equal(s.rerank, false); // stored value wins
  assert.equal(s.autoRead, true); // default filled
  assert.equal(s.weights.like, 9); // stored weight
  assert.equal(s.weights.hide, -5); // missing weight backfilled
});

test("feedback round-trips", async () => {
  backing.clear();
  const fb = { "x/p/a": { like: true, read: false, hide: false, notint: false } };
  assert.equal(await PaiaStore.setFeedback(fb), true);
  assert.deepEqual(await PaiaStore.getFeedback(), fb);
});

test("migration records the schema version", async () => {
  backing.clear();
  await PaiaStore.init();
  assert.equal(backing.get("paia.ext.schema"), String(PaiaStore.SCHEMA_VERSION));
});

test("export produces a tagged object; import restores it", async () => {
  backing.clear();
  await PaiaStore.setFeedback({ "x/p/a": { like: true } });
  await PaiaStore.setSettings({ weights: { like: 7, read: 1, notint: -3, hide: -5 } });
  const dump = await PaiaStore.exportData();
  assert.equal(dump.app, "daily-briefing-paia");
  assert.equal(dump.schema, PaiaStore.SCHEMA_VERSION);

  backing.clear();
  const ok = await PaiaStore.importData(dump);
  assert.equal(ok, true);
  assert.deepEqual(await PaiaStore.getFeedback(), { "x/p/a": { like: true } });
  assert.equal((await PaiaStore.getSettings()).weights.like, 7);
});

test("importData rejects malformed input", async () => {
  await assert.rejects(() => PaiaStore.importData(null));
  await assert.rejects(() => PaiaStore.importData({ feedback: "nope" }));
});

test("a failed write returns false and fires onError instead of throwing", async () => {
  backing.clear();
  let errored = false;
  PaiaStore.onError(() => (errored = true));
  throwOnSet = true;
  const ok = await PaiaStore.setFeedback({ "x/p/a": { like: true } });
  throwOnSet = false;
  PaiaStore.onError(null);
  assert.equal(ok, false);
  assert.equal(errored, true);
});
