/* Daily Briefing pAIa — storage adapter.
 * Uses chrome.storage.local inside the extension; falls back to localStorage
 * when chrome APIs are absent (so the same code runs in the test harness).
 * All values are namespaced and everything stays on the user's device.
 *
 * Resilience (v0.5):
 *  - a stored schema version + migration path, so future shape changes don't
 *    wipe existing data;
 *  - writes never throw — a failed save (quota, blocked storage) is caught,
 *    reported via onError, and returns false instead of breaking the feed;
 *  - export / import of signals as JSON.
 */
(function (g) {
  "use strict";

  const SCHEMA_VERSION = 1;
  const K = { feedback: "feedback", settings: "settings", snapshot: "snapshot", schema: "schema" };
  const hasChrome = typeof chrome !== "undefined" && chrome.storage && chrome.storage.local;

  let errorHandler = null;

  async function get(key, def) {
    try {
      if (hasChrome) {
        const r = await chrome.storage.local.get(key);
        return r[key] === undefined ? def : r[key];
      }
      const v = localStorage.getItem("paia.ext." + key);
      return v == null ? def : JSON.parse(v);
    } catch (e) {
      console.warn("pAIa: failed to read", key, e && e.message);
      return def;
    }
  }

  // Never throws. Returns true on success, false on failure (e.g. quota
  // exceeded), so callers can surface a problem without the page breaking.
  async function set(key, val) {
    try {
      if (hasChrome) {
        await chrome.storage.local.set({ [key]: val });
      } else {
        localStorage.setItem("paia.ext." + key, JSON.stringify(val));
      }
      return true;
    } catch (e) {
      console.warn("pAIa: failed to save", key, e && e.message);
      if (errorHandler) {
        try { errorHandler(key, e); } catch (_) {}
      }
      return false;
    }
  }

  const DEFAULT_SETTINGS = {
    rerank: true,
    sort: "recommended",
    autoRead: true,
    showHidden: false,
    weights: { like: 3, read: 1, notint: -3, hide: -5 },
  };

  // Bring stored data up to the current schema. Idempotent and safe to call from
  // any context. Future changes add `while (v < N) { ...transform...; v++ }`.
  async function migrate() {
    let v = await get(K.schema, 0);
    if (v >= SCHEMA_VERSION) return;
    // v0 -> v1: no shape change; existing feedback/settings are already
    // v1-compatible, and getSettings backfills any missing keys (e.g. weights).
    await set(K.schema, SCHEMA_VERSION);
  }

  async function getSettings() {
    const s = Object.assign({}, DEFAULT_SETTINGS, await get(K.settings, {}));
    // deep-fill weights so settings saved before weights existed still work
    s.weights = Object.assign({}, DEFAULT_SETTINGS.weights, s.weights || {});
    return s;
  }

  async function exportData() {
    const [feedback, settings] = await Promise.all([get(K.feedback, {}), get(K.settings, {})]);
    return { app: "daily-briefing-paia", schema: SCHEMA_VERSION, exportedAt: new Date().toISOString(), feedback, settings };
  }

  // Accepts an object from exportData (or a bare {feedback, settings}). Validates
  // lightly and only writes recognized shapes.
  async function importData(obj) {
    if (!obj || typeof obj !== "object") throw new Error("Invalid file: not an object");
    if (obj.feedback && typeof obj.feedback !== "object") throw new Error("Invalid file: bad feedback");
    if (obj.settings && typeof obj.settings !== "object") throw new Error("Invalid file: bad settings");
    let ok = true;
    if (obj.feedback) ok = (await set(K.feedback, obj.feedback)) && ok;
    if (obj.settings) ok = (await set(K.settings, obj.settings)) && ok;
    await set(K.schema, SCHEMA_VERSION);
    return ok;
  }

  g.PaiaStore = {
    SCHEMA_VERSION,
    init: migrate,
    getFeedback: () => get(K.feedback, {}),
    setFeedback: (v) => set(K.feedback, v),
    getSettings,
    setSettings: (v) => set(K.settings, v),
    getSnapshot: () => get(K.snapshot, []),
    setSnapshot: (v) => set(K.snapshot, v),
    exportData,
    importData,
    onChange: (cb) => { if (hasChrome) chrome.storage.onChanged.addListener(cb); },
    onError: (cb) => { errorHandler = cb; },
    hasChrome,
  };

  // Run the migration once when the module loads (idempotent across contexts).
  migrate();
})(typeof self !== "undefined" ? self : this);
