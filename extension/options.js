/* Daily Briefing pAIa — options page.
 * Reads/writes settings and feedback via the shared storage adapter. Changes
 * take effect on open feeds live (the content script reloads on storage change).
 */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  const DEFAULT_WEIGHTS = { like: 3, read: 1, notint: -3, hide: -5 };

  // In-memory source of truth (loaded once in init). Mutating this synchronously
  // and persisting the whole object avoids a read-modify-write race when several
  // settings change in quick succession.
  let settings = null;

  let savedTimer;
  function flashSaved() {
    const el = $("#saved");
    el.classList.add("show");
    clearTimeout(savedTimer);
    savedTimer = setTimeout(() => el.classList.remove("show"), 1200);
  }

  function save(patch) {
    Object.assign(settings, patch);
    PaiaStore.setSettings(settings);
    flashSaved();
  }

  function readWeights() {
    return {
      like: Number($("#w-like").value) || 0,
      read: Number($("#w-read").value) || 0,
      notint: Number($("#w-notint").value) || 0,
      hide: Number($("#w-hide").value) || 0,
    };
  }
  function fillWeights(w) {
    $("#w-like").value = w.like;
    $("#w-read").value = w.read;
    $("#w-notint").value = w.notint;
    $("#w-hide").value = w.hide;
  }

  async function renderDataSummary() {
    const fb = await PaiaStore.getFeedback();
    let read = 0, like = 0, notint = 0, hide = 0;
    Object.values(fb).forEach((f) => {
      if (!f) return;
      if (f.read) read++;
      if (f.like) like++;
      if (f.notint) notint++;
      if (f.hide) hide++;
    });
    const total = Object.keys(fb).length;
    $("#data-summary").textContent =
      total === 0
        ? "No feedback stored yet."
        : `${total} posts with signals — ${like} liked, ${read} read, ${notint} not-interesting, ${hide} hidden.`;
  }

  function applyToForm() {
    $("#rerank").checked = !!settings.rerank;
    $("#sort").value = settings.sort || "recommended";
    $("#autoRead").checked = !!settings.autoRead;
    $("#showHidden").checked = !!settings.showHidden;
    fillWeights(settings.weights || DEFAULT_WEIGHTS);
  }

  async function init() {
    settings = await PaiaStore.getSettings();
    applyToForm();
    renderDataSummary();

    $("#rerank").addEventListener("change", (e) => save({ rerank: e.target.checked }));
    $("#sort").addEventListener("change", (e) => save({ sort: e.target.value }));
    $("#autoRead").addEventListener("change", (e) => save({ autoRead: e.target.checked }));
    $("#showHidden").addEventListener("change", (e) => save({ showHidden: e.target.checked }));

    ["#w-like", "#w-read", "#w-notint", "#w-hide"].forEach((sel) =>
      $(sel).addEventListener("change", () => save({ weights: readWeights() }))
    );
    $("#reset-weights").addEventListener("click", () => {
      fillWeights(DEFAULT_WEIGHTS);
      save({ weights: Object.assign({}, DEFAULT_WEIGHTS) });
    });

    $("#reset-data").addEventListener("click", async () => {
      if (!confirm("Reset all feedback? This clears every like/read/hide signal on this device.")) return;
      await PaiaStore.setFeedback({});
      renderDataSummary();
      flashSaved();
    });

    // Export: download signals as a JSON file.
    $("#export-data").addEventListener("click", async () => {
      const data = await PaiaStore.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "daily-briefing-paia-signals.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      setStatus("Exported.");
    });

    // Import: read a JSON file and merge it in.
    $("#import-data").addEventListener("click", () => $("#import-file").click());
    $("#import-file").addEventListener("change", async (e) => {
      const file = e.target.files && e.target.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const obj = JSON.parse(text);
        const ok = await PaiaStore.importData(obj);
        settings = await PaiaStore.getSettings(); // reflect imported settings
        applyToForm();
        renderDataSummary();
        setStatus(ok ? "Imported." : "Imported, but some data couldn't be saved.");
        flashSaved();
      } catch (err) {
        setStatus("Import failed: " + (err && err.message ? err.message : "invalid file"));
      } finally {
        e.target.value = ""; // allow re-importing the same file
      }
    });
  }

  function setStatus(msg) {
    const el = $("#io-status");
    if (el) el.textContent = msg || "";
  }

  // Scripts load at end of <body>, so the DOM is ready; run once and guard
  // against a duplicate DOMContentLoaded firing (which would double-bind listeners).
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
