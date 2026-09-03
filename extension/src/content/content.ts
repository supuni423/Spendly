import { detectProduct } from "./productDetector";
import type { DetectedProduct } from "@/types/product";

export {};

// Injected on demand (via chrome.scripting.executeScript) each time the
// popup opens on this tab. The injected context persists per-tab until
// navigation, so a repeat popup-open on the same page re-injects the same
// script — guard against re-registering the listener below.
if (!(window as unknown as { __spendlyContentLoaded?: boolean }).__spendlyContentLoaded) {
  (window as unknown as { __spendlyContentLoaded?: boolean }).__spendlyContentLoaded = true;

  let cachedProduct: DetectedProduct | null = null;

  function runDetection(): void {
    cachedProduct = detectProduct();
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    if (message?.type === "SPENDLY_GET_DETECTED_PRODUCT") {
      sendResponse({ product: cachedProduct });
    }
    return true;
  });

  if (document.readyState === "complete" || document.readyState === "interactive") {
    runDetection();
  } else {
    window.addEventListener("DOMContentLoaded", runDetection);
  }
}
