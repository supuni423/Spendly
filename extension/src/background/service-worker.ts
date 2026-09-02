/**
 * Background service worker. Routes messages between the content script
 * and popup. Holds only the user's auth token (via chromeStorage) — never
 * LLM provider keys, database credentials, or signing secrets. Those live
 * exclusively on the backend (Section 9).
 */

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.type === "SPENDLY_ANALYZE_REQUEST") {
    // Phase 8 wires this to POST /api/analysis via src/api/analysisApi.ts.
    // No backend exists yet, so this is intentionally a stub.
    sendResponse({ status: "not_implemented" });
    return true;
  }
  return false;
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({ text: "" });
});
