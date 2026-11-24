/* Daily Briefing pAIa — federated client (Stage 3 prototype).
 *
 * The client half of networked federated learning: send only this device's
 * learned term weights to the coordinator, then pull back the averaged global
 * model. Raw feedback never travels. Isomorphic (browser + Node), uses fetch,
 * and would run from the extension's service worker behind an opt-in setting and
 * a host permission for the coordinator's origin — it is NOT wired into the
 * shipped extension yet.
 */
(function (g) {
  "use strict";

  const hasFetch = typeof fetch === "function";

  // POST this client's update ({clientId, termAff, samples}) to the coordinator.
  async function submitUpdate(baseUrl, clientId, update, opts) {
    if (!hasFetch) throw new Error("fetch unavailable");
    const body = JSON.stringify({
      clientId: String(clientId),
      termAff: (update && update.termAff) || {},
      samples: (update && update.samples) || 0,
    });
    const res = await fetch(baseUrl.replace(/\/$/, "") + "/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      signal: opts && opts.signal,
    });
    if (!res.ok) throw new Error("submit failed: " + res.status);
    return res.json();
  }

  // GET the current FedAvg global model, usable directly by PaiaTopic.score.
  async function fetchGlobalModel(baseUrl, opts) {
    if (!hasFetch) throw new Error("fetch unavailable");
    const res = await fetch(baseUrl.replace(/\/$/, "") + "/model", { signal: opts && opts.signal });
    if (!res.ok) throw new Error("model fetch failed: " + res.status);
    const data = await res.json();
    // Shape it like a topic model (N:0 => uniform IDF, matching the coordinator).
    return { termAff: data.termAff || {}, N: 0, df: {}, clients: data.clients || 0, round: data.round };
  }

  // Convenience: submit this client's update, then return the fresh global model.
  async function syncRound(baseUrl, clientId, update, opts) {
    await submitUpdate(baseUrl, clientId, update, opts);
    return fetchGlobalModel(baseUrl, opts);
  }

  const api = { submitUpdate, fetchGlobalModel, syncRound };
  g.PaiaFLClient = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof self !== "undefined" ? self : this);
