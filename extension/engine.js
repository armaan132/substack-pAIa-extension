/* Daily Briefing pAIa — shared ranking engine.
 * Pure functions. Loaded in the content script, the popup, and the service
 * worker (which share it via the same global object). No DOM, no storage here.
 */
(function (g) {
  "use strict";

  // Default weights for how much each action shifts affinity. Users can override
  // these from the options page; functions accept an optional `weights` arg.
  const WEIGHTS = { like: 3, read: 1, notint: -3, hide: -5 };

  function weightOf(f, weights) {
    const W = weights || WEIGHTS;
    if (!f) return 0;
    let w = 0;
    if (f.like) w += W.like;
    if (f.read) w += W.read;
    if (f.notint) w += W.notint;
    if (f.hide) w += W.hide;
    return w;
  }

  // Roll all feedback up into per-publication and per-author affinity scores.
  function buildAffinities(posts, feedback, weights) {
    const pub = {}, author = {};
    const bump = (m, k, w) => { if (k) m[k] = (m[k] || 0) + w; };
    for (const p of posts) {
      const w = weightOf(feedback[p.id], weights);
      if (!w) continue;
      bump(pub, p.publication, w);
      bump(author, p.author, w);
    }
    return { pub, author };
  }

  // Newer posts get a small, decaying boost so a cold-start feed still sorts
  // sensibly. Returns 0 when the date can't be parsed.
  function freshness(publishedAt) {
    const t = publishedAt ? Date.parse(publishedAt) : NaN;
    if (isNaN(t)) return 0;
    const days = Math.max(0, (Date.now() - t) / 86400000);
    return Math.max(0, 2 - days * 0.25);
  }

  function firstName(n) { return (n || "").split(/\s+/)[0]; }

  function scorePost(post, aff, feedback) {
    const f = feedback[post.id] || {};
    const pubS = aff.pub[post.publication] || 0;
    const authS = aff.author[post.author] || 0;

    let score = pubS * 1.0 + authS * 0.6 + freshness(post.publishedAt);
    if (f.like) score += 2;
    if (f.notint) score -= 4;
    if (f.hide) score -= 100; // effectively drops it to the bottom

    const reasons = [];
    if (pubS) reasons.push((pubS > 0 ? "+" : "") + pubS + " " + post.publication);
    if (authS > 0 && post.author && post.author !== post.publication) reasons.push("likes " + firstName(post.author));
    if (f.like) reasons.push("you liked this");
    if (f.notint) reasons.push("not interested");
    if (!reasons.length) reasons.push("baseline + freshness");
    return { score, reasons };
  }

  function rank(posts, feedback, weights) {
    const aff = buildAffinities(posts, feedback, weights);
    return posts
      .map((p) => ({ post: p, ...scorePost(p, aff, feedback) }))
      .sort((a, b) => b.score - a.score);
  }

  g.PaiaEngine = { WEIGHTS, weightOf, buildAffinities, scorePost, rank, freshness };
})(typeof self !== "undefined" ? self : this);
