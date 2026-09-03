/**
 * Background service worker. Routes messages between the content script
 * and popup. Holds only the user's auth token (via chromeStorage) — never
 * LLM provider keys, database credentials, or signing secrets. Those live
 * exclusively on the backend (Section 9).
 *
 * Analysis itself is never run here — the popup is the only UI (Section 3),
 * so it owns the fetch + render logic. This worker's job when the in-page
 * "Analyze with Spendly" button is clicked is just to bring the popup up.
 */

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "SPENDLY_ANALYZE_REQUEST") {
    chrome.action.openPopup().catch(() => {
      // openPopup() requires a fairly recent Chrome and a live user
      // gesture context; if it's unavailable, the user can still click
      // the toolbar icon directly — the popup always re-detects the
      // product itself on open.
    });
    sendResponse({ status: "ok" });
    return true;
  }
  return false;
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({ text: "" });
});
