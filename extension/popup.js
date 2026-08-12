/* Daily Briefing pAIa — popup dashboard.
 * Reflects the feedback and the last-scraped snapshot from storage: counts,
 * publication affinity, and the top ranked posts. Also mirrors the settings.
 */
(function () {
  "use strict";
  const $ = (s) => document.querySelector(s);
  let currentSettings = {}; // in-memory settings so the change handlers don't race

  async function render() {
    const [feedback, snapshot, settings] = await Promise.all([
      PaiaStore.getFeedback(),
      PaiaStore.getSnapshot(),
      PaiaStore.getSettings(),
    ]);

    currentSettings = settings; // in-memory source of truth for the handlers below
    $("#rerank").checked = !!settings.rerank;
    $("#sort").value = settings.sort || "recommended";

    // Counts
    let read = 0, like = 0, notint = 0, hide = 0;
    Object.values(feedback).forEach((f) => {
      if (!f) return;
      if (f.read) read++;
      if (f.like) like++;
      if (f.notint) notint++;
      if (f.hide) hide++;
    });
    $("#stats").innerHTML = [
      ["Read", read], ["Liked", like], ["Not int.", notint], ["Hidden", hide],
    ].map(([k, n]) => `<div class="stat"><div class="n">${n}</div><div class="k">${k}</div></div>`).join("");

    // Affinity (publication)
    const aff = PaiaEngine.buildAffinities(snapshot, feedback, settings.weights);
    const entries = Object.entries(aff.pub).sort((a, b) => b[1] - a[1]);
    if (!entries.length) {
      $("#affinity").innerHTML = `<p class="empty">No signals yet. Like, read, or hide posts on a Substack feed to train your ranking.</p>`;
    } else {
      const max = Math.max(1, ...entries.map(([, v]) => Math.abs(v)));
      $("#affinity").innerHTML = entries.map(([name, v]) => {
        const pct = Math.round((Math.abs(v) / max) * 100);
        const cls = v >= 0 ? "pos" : "neg";
        return `<div class="aff"><div class="lbl"><span>${name}</span><span>${v > 0 ? "+" : ""}${v}</span></div>
          <div class="bar"><div class="fill ${cls}" style="width:${pct}%"></div></div></div>`;
      }).join("");
    }

    // Top ranked
    if (!snapshot.length) {
      $("#ranked").innerHTML = `<p class="empty">Once you visit a Substack feed, your ranked posts show up here.</p>`;
    } else {
      const ranked = PaiaEngine.rank(snapshot, feedback, settings.weights).slice(0, 6);
      $("#ranked").innerHTML = ranked.map(({ post, score, reasons }, i) =>
        `<a class="rank" href="${post.url}" target="_blank" rel="noopener">
          <span class="rk">${i + 1}</span>
          <span class="info"><span class="t">${escapeHtml(post.title || post.publication)}</span>
          <span class="why">${escapeHtml(reasons.join(" · "))}</span></span>
          <span class="sc">${score.toFixed(1)}</span>
        </a>`).join("");
    }
  }

  function escapeHtml(s) {
    return (s || "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  $("#rerank").addEventListener("change", (e) => {
    currentSettings.rerank = e.target.checked;
    PaiaStore.setSettings(currentSettings);
  });
  $("#sort").addEventListener("change", (e) => {
    currentSettings.sort = e.target.value;
    PaiaStore.setSettings(currentSettings);
  });
  $("#reset").addEventListener("click", async () => {
    await PaiaStore.setFeedback({});
    render();
  });
  const optionsLink = $("#options-link");
  if (optionsLink) {
    optionsLink.addEventListener("click", (e) => {
      e.preventDefault();
      if (typeof chrome !== "undefined" && chrome.runtime && chrome.runtime.openOptionsPage) {
        chrome.runtime.openOptionsPage();
      } else {
        window.open("options.html", "_blank");
      }
    });
  }

  PaiaStore.onChange(render);
  document.addEventListener("DOMContentLoaded", render);
  render();
})();
