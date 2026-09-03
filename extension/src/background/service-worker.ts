/**
 * Background service worker. Holds only the user's auth token (via
 * chromeStorage) — never LLM provider keys, database credentials, or
 * signing secrets. Those live exclusively on the backend (Section 9).
 *
 * Analysis itself is never run here — the popup is the only UI (Section 3),
 * and it also owns content-script injection (via activeTab, triggered by
 * the popup-open gesture) and detection/fetch/render. This worker has no
 * standing job beyond extension lifecycle housekeeping.
 */

chrome.runtime.onInstalled.addListener(() => {
  chrome.action.setBadgeText({ text: "" });
});
