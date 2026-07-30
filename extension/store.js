/* Daily Briefing pAIa — storage adapter.
 * Uses chrome.storage.local inside the extension; falls back to localStorage
 * when chrome APIs are absent (so the same code runs in the test harness).
 * All values are namespaced and everything stays on the user's device.
 */
(function (g) {
  "use strict";

  const K = { feedback: "feedback", settings: "settings", snapshot: "snapshot" };
  const hasChrome = typeof chrome !== "undefined" && chrome.storage && chrome.storage.local;

  async function get(key, def) {
    if (hasChrome) {
      const r = await chrome.storage.local.get(key);
      return r[key] === undefined ? def : r[key];
    }
    try {
      const v = localStorage.getItem("paia.ext." + key);
      return v == null ? def : JSON.parse(v);
    } catch {
      return def;
    }
  }

  async function set(key, val) {
    if (hasChrome) return chrome.storage.local.set({ [key]: val });
    localStorage.setItem("paia.ext." + key, JSON.stringify(val));
  }

  const DEFAULT_SETTINGS = { rerank: true, sort: "recommended" };

  g.PaiaStore = {
    getFeedback: () => get(K.feedback, {}),
    setFeedback: (v) => set(K.feedback, v),
    getSettings: async () => Object.assign({}, DEFAULT_SETTINGS, await get(K.settings, {})),
    setSettings: (v) => set(K.settings, v),
    getSnapshot: () => get(K.snapshot, []),
    setSnapshot: (v) => set(K.snapshot, v),
    onChange: (cb) => { if (hasChrome) chrome.storage.onChanged.addListener(cb); },
    hasChrome,
  };
})(typeof self !== "undefined" ? self : this);
