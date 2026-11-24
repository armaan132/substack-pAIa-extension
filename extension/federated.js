/* Daily Briefing pAIa — federated aggregation (Stage 2 prototype).
 *
 * Federated learning in one sentence: each client trains a model on its OWN
 * data and shares only the learned parameters (weights); a coordinator averages
 * those into a global model and sends it back — the raw data never leaves the
 * client. This module is the coordinator's math: Federated Averaging (FedAvg)
 * over the topic model's per-term affinity vectors (see topic.js).
 *
 * Stage 2 is a *simulation*: several on-device profiles stand in for several
 * clients, so there is still no network and nothing leaves the device. It
 * demonstrates the mechanic — and the privacy property — that Stage 3 (real,
 * networked FL) would build on. Crucially, a client "update" carries only a
 * term->weight vector and a sample count; it contains no feedback, post ids, or
 * titles, which is exactly what makes FL privacy-preserving.
 *
 * Pure functions, no DOM / storage / network — like engine.js and topic.js.
 */
(function (g) {
  "use strict";

  // Turn a locally-trained topic model into a shareable client update. Only the
  // learned term weights leave the client, plus a sample count so the
  // coordinator can weight larger clients more (standard FedAvg). The raw
  // feedback that produced `termAff` stays behind.
  function toUpdate(topicModel, samples) {
    const termAff = (topicModel && topicModel.termAff) || {};
    // Shallow-copy so later local training can't mutate an already-sent update.
    const copy = Object.create(null);
    for (const t in termAff) copy[t] = termAff[t];
    const n = Number(samples);
    return { termAff: copy, samples: Number.isFinite(n) && n > 0 ? n : 0 };
  }

  // Federated Averaging: a sample-weighted mean of the clients' term vectors.
  // Each term's global weight is sum_i(w_i * aff_i) / sum_i(w_i), where w_i is
  // client i's sample count (falling back to equal weights when no client
  // reports samples). Returns a model usable directly by PaiaTopic.score.
  function aggregate(updates) {
    const list = (updates || []).filter((u) => u && u.termAff);
    const termAff = Object.create(null);
    if (!list.length) return { termAff, N: 0, df: Object.create(null), clients: 0 };

    const totalSamples = list.reduce((s, u) => s + (u.samples > 0 ? u.samples : 0), 0);
    const useSamples = totalSamples > 0;
    const denom = useSamples ? totalSamples : list.length;

    for (const u of list) {
      const w = (useSamples ? (u.samples > 0 ? u.samples : 0) : 1) / denom;
      if (!w) continue;
      for (const t in u.termAff) termAff[t] = (termAff[t] || 0) + w * u.termAff[t];
    }
    // N:0 => PaiaTopic.score falls back to uniform IDF, which is correct here:
    // the coordinator averages weights, not corpora, so it holds no document
    // frequencies of its own.
    return { termAff, N: 0, df: Object.create(null), clients: list.length };
  }

  // Convenience: run one federated round from already-built client updates.
  // (Kept thin so the round is easy to reason about and test.)
  function round(updates) {
    return aggregate(updates);
  }

  g.PaiaFederated = { toUpdate, aggregate, round };
})(typeof self !== "undefined" ? self : this);
