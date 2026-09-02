import { detectProduct } from "./productDetector";
import type { DetectedProduct } from "@/types/product";

let cachedProduct: DetectedProduct | null = null;

function injectAnalyzeButton(product: DetectedProduct): void {
  if (document.getElementById("spendly-analyze-button")) return;

  const button = document.createElement("button");
  button.id = "spendly-analyze-button";
  button.className = "spendly-analyze-button";
  button.type = "button";
  button.textContent = "🧠 Analyze with Spendly";
  button.addEventListener("click", () => {
    chrome.runtime.sendMessage({ type: "SPENDLY_ANALYZE_REQUEST", product });
  });

  document.body.appendChild(button);
}

function runDetection(): void {
  cachedProduct = detectProduct();
  if (cachedProduct) {
    injectAnalyzeButton(cachedProduct);
  }
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
