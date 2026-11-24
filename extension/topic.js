/* Daily Briefing pAIa — on-device topic model (Stage 1 ML).
 *
 * A small, transparent content-based model: it learns which *topics* (words in
 * post titles) you engage with, so recommendations generalize beyond the exact
 * publications/authors you've rated. This is a learned TF-IDF bag-of-words model
 * — a classic content-based recommender — implemented in plain JS. It trains on
 * your own feedback, runs entirely on your device, and ships no external code.
 *
 * Pipeline:
 *   tokenize   -> split a title into lowercased content words (stopwords dropped)
 *   buildModel -> from rated posts, learn a per-term affinity vector (TF-weighted
 *                 feedback) plus document frequencies for IDF
 *   score      -> for a candidate post, a TF-IDF-weighted average of its terms'
 *                 learned affinities, with the terms that drove the score
 *
 * Pure functions, no DOM and no storage — same as engine.js, so the content
 * script, popup, and tests can all share it.
 */
(function (g) {
  "use strict";

  // Common words that carry no topic signal. Kept short on purpose: the IDF term
  // weighting already demotes words that appear in most titles.
  const STOP = new Set(
    ("a an and are as at be but by for from has have how i in into is it its of on" +
      " or that the their they this to was what when which who why will with you your" +
      " we our us my me he she his her them then than so if not no yes do does did" +
      " new get vs via").split(/\s+/)
  );

  // How many top terms to surface as the human-readable reason ("why this rank").
  const TOP_TERMS = 2;

  // Lowercase, keep letter runs of length >= 3, drop stopwords. Deliberately
  // simple and deterministic (no stemming) so behavior is easy to reason about.
  function tokenize(text) {
    if (!text) return [];
    const out = [];
    const raw = String(text).toLowerCase().match(/[a-z][a-z'-]{2,}/g) || [];
    for (let w of raw) {
      w = w.replace(/^['-]+|['-]+$/g, "");
      if (w.length >= 3 && !STOP.has(w)) out.push(w);
    }
    return out;
  }

  // Term frequencies within one document, normalized so each title contributes
  // the same total mass regardless of length (sum of tf === 1).
  function termFreq(tokens) {
    const tf = Object.create(null);
    if (!tokens.length) return tf;
    for (const t of tokens) tf[t] = (tf[t] || 0) + 1;
    const n = tokens.length;
    for (const t in tf) tf[t] /= n;
    return tf;
  }

  // Learn the model from the current feed + the user's feedback.
  //   weightOf: fn(feedback_entry) -> signed number (reuse engine.weightOf so the
  //             user's custom weights apply identically here).
  // Returns { termAff, df, N } where termAff[term] is the accumulated, TF-weighted
  // feedback mass for that term across all rated posts.
  function buildModel(posts, feedback, weightOf) {
    const termAff = Object.create(null);
    const df = Object.create(null);
    const wf = typeof weightOf === "function" ? weightOf : () => 0;
    let N = 0;
    for (const p of posts || []) {
      const tokens = tokenize(p && p.title);
      if (!tokens.length) continue;
      N++;
      const tf = termFreq(tokens);
      for (const t in tf) df[t] = (df[t] || 0) + 1; // document frequency
      const w = wf(feedback ? feedback[p.id] : undefined);
      if (!w) continue; // unrated post still counts toward df (corpus), not affinity
      for (const t in tf) termAff[t] = (termAff[t] || 0) + w * tf[t];
    }
    return { termAff, df, N };
  }

  // Inverse document frequency, smoothed so unseen/rare terms stay finite.
  function idf(term, model) {
    const N = model && model.N ? model.N : 0;
    const d = (model && model.df && model.df[term]) || 0;
    return Math.log((N + 1) / (d + 1)) + 1;
  }

  // Score a candidate post against the learned model. Returns:
  //   { score, top } — score is a TF-IDF-weighted average of its terms' learned
  //   affinities (0 when nothing is known); top is up to TOP_TERMS driving words.
  function score(post, model) {
    const empty = { score: 0, top: [] };
    if (!model || !model.termAff) return empty;
    const tokens = tokenize(post && post.title);
    if (!tokens.length) return empty;
    const tf = termFreq(tokens);
    let s = 0;
    const contrib = [];
    for (const t in tf) {
      const aff = model.termAff[t];
      if (!aff) continue;
      const c = tf[t] * idf(t, model) * aff; // TF-IDF-weighted learned affinity
      s += c;
      contrib.push([t, c]);
    }
    contrib.sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
    const top = contrib.slice(0, TOP_TERMS).map((c) => c[0]);
    return { score: s, top };
  }

  g.PaiaTopic = { tokenize, buildModel, score, TOP_TERMS };
})(typeof self !== "undefined" ? self : this);
