import { useEffect, useState } from "react";
import type { DetectedProduct } from "@/types/product";
import { formatPrice } from "@/utils/priceFormatting";
import "./popup.css";

type PopupState =
  | { status: "loading" }
  | { status: "no-product" }
  | { status: "detected"; product: DetectedProduct }
  | { status: "analyzing"; product: DetectedProduct }
  | { status: "not-implemented"; product: DetectedProduct };

async function getActiveTabProduct(): Promise<DetectedProduct | null> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return null;

  try {
    const response = await chrome.tabs.sendMessage(tab.id, {
      type: "SPENDLY_GET_DETECTED_PRODUCT",
    });
    return response?.product ?? null;
  } catch {
    // No content script on this page (e.g. chrome:// pages, unsupported site).
    return null;
  }
}

export function Popup() {
  const [state, setState] = useState<PopupState>({ status: "loading" });

  useEffect(() => {
    getActiveTabProduct().then((product) => {
      setState(product ? { status: "detected", product } : { status: "no-product" });
    });
  }, []);

  async function handleAnalyze(product: DetectedProduct) {
    setState({ status: "analyzing", product });
    await chrome.runtime.sendMessage({ type: "SPENDLY_ANALYZE_REQUEST", product });
    setState({ status: "not-implemented", product });
  }

  return (
    <div className="spendly-popup">
      <header className="spendly-header">
        <span className="spendly-logo">🧠 Spendly</span>
      </header>

      {state.status === "loading" && <p className="spendly-muted">Checking this page…</p>}

      {state.status === "no-product" && (
        <p className="spendly-muted">
          No product detected on this page. Open a product page and reopen Spendly.
        </p>
      )}

      {(state.status === "detected" ||
        state.status === "analyzing" ||
        state.status === "not-implemented") && (
        <div className="spendly-product-card">
          <h2>{state.product.productName}</h2>
          {state.product.price !== null && (
            <p className="spendly-price">
              {formatPrice(state.product.price, state.product.currency ?? "LKR")}
            </p>
          )}
          {state.product.brand && <p className="spendly-muted">{state.product.brand}</p>}

          <button
            className="spendly-analyze-btn"
            disabled={state.status === "analyzing"}
            onClick={() => handleAnalyze(state.product)}
          >
            {state.status === "analyzing" ? "Analyzing…" : "Analyze with Spendly"}
          </button>

          {state.status === "not-implemented" && (
            <p className="spendly-muted spendly-note">
              Backend intelligence isn't connected yet — this ships in a later phase.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
