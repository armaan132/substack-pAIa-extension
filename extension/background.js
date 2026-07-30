/* Daily Briefing pAIa — service worker (MV3).
 * Seeds default settings on install and keeps the toolbar badge showing how
 * many posts you've liked. The ranking engine is shared but the heavy lifting
 * happens in the content script, on the page.
 */
importScripts("engine.js", "store.js");

async function refreshBadge() {
  const fb = await PaiaStore.getFeedback();
  const liked = Object.values(fb).filter((f) => f && f.like).length;
  chrome.action.setBadgeText({ text: liked ? String(liked) : "" });
  chrome.action.setBadgeBackgroundColor({ color: "#1f9d57" });
}

chrome.runtime.onInstalled.addListener(async () => {
  const s = await PaiaStore.getSettings();
  await PaiaStore.setSettings(s); // persist defaults
  refreshBadge();
});

chrome.storage.onChanged.addListener((changes, area) => {
  if (area === "local" && changes.feedback) refreshBadge();
});
