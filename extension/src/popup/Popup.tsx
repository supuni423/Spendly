import { useEffect, useState } from "react";
import type { DetectedProduct } from "@/types/product";
import type { AnalysisResult } from "@/types/analysis";
import { clearAuthToken, getAuthToken } from "@/storage/chromeStorage";
import { analyzeProduct } from "@/api/analysisApi";
import { ApiError } from "@/api/apiClient";
import { formatPrice } from "@/utils/priceFormatting";
import { AuthForm } from "@/components/AuthForm";
import { LoadingState } from "@/components/LoadingState";
import { RecommendationCard } from "@/components/RecommendationCard";
import { SpendingSummary } from "@/components/SpendingSummary";
import { SimilarProducts } from "@/components/SimilarProducts";
import { PriceComparisonCard } from "@/components/PriceComparisonCard";
import contentScriptPath from "../content/content.ts?script";
import "./popup.css";

type PopupState =
  | { status: "checking-auth" }
  | { status: "needs-auth" }
  | { status: "checking-product" }
  | { status: "no-product" }
  | { status: "unsupported-page" }
  | { status: "detected"; product: DetectedProduct }
  | { status: "analyzing"; product: DetectedProduct }
  | { status: "result"; product: DetectedProduct; result: AnalysisResult }
  | { status: "error"; product: DetectedProduct; message: string };

type DetectionOutcome =
  | { status: "detected"; product: DetectedProduct }
  | { status: "no-product" }
  | { status: "unsupported-page" };

async function requestDetectedProduct(tabId: number): Promise<DetectedProduct | null> {
  const response = await chrome.tabs.sendMessage(tabId, {
    type: "SPENDLY_GET_DETECTED_PRODUCT",
  });
  return response?.product ?? null;
}

async function getActiveTabProduct(): Promise<DetectionOutcome> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return { status: "unsupported-page" };
  const tabId = tab.id;

  // The content script may already be alive in this tab from a previous
  // popup-open on the same page — probe first so we don't re-inject and
  // stack a second listener.
  try {
    const product = await requestDetectedProduct(tabId);
    return product ? { status: "detected", product } : { status: "no-product" };
  } catch {
    // No content script listening yet — fall through and inject one.
  }

  try {
    await chrome.scripting.executeScript({ target: { tabId }, files: [contentScriptPath] });
  } catch {
    // chrome:// pages, the Web Store, the PDF viewer, etc. — activeTab
    // scripting isn't allowed there.
    return { status: "unsupported-page" };
  }

  try {
    const product = await requestDetectedProduct(tabId);
    return product ? { status: "detected", product } : { status: "no-product" };
  } catch {
    return { status: "no-product" };
  }
}

export function Popup() {
  const [state, setState] = useState<PopupState>({ status: "checking-auth" });

  async function detectProduct() {
    setState({ status: "checking-product" });
    setState(await getActiveTabProduct());
  }

  useEffect(() => {
    getAuthToken().then((token) => {
      if (token) {
        detectProduct();
      } else {
        setState({ status: "needs-auth" });
      }
    });
  }, []);

  async function handleAnalyze(product: DetectedProduct) {
    setState({ status: "analyzing", product });
    try {
      const result = await analyzeProduct(product);
      setState({ status: "result", product, result });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        await clearAuthToken();
        setState({ status: "needs-auth" });
        return;
      }
      const message =
        err instanceof ApiError
          ? err.message
          : "Couldn't reach Spendly. Check that the backend is running.";
      setState({ status: "error", product, message });
    }
  }

  return (
    <div className="spendly-popup">
      <header className="spendly-header">
        <span className="spendly-logo">🧠 Spendly</span>
      </header>

      {state.status === "checking-auth" && <LoadingState label="Loading…" />}

      {state.status === "needs-auth" && <AuthForm onAuthenticated={detectProduct} />}

      {state.status === "checking-product" && <LoadingState label="Checking this page…" />}

      {state.status === "no-product" && (
        <p className="spendly-muted">
          No product detected on this page. Open a product page and reopen Spendly.
        </p>
      )}

      {state.status === "unsupported-page" && (
        <p className="spendly-muted">
          Spendly can't run on this page. Open a shopping site and reopen Spendly.
        </p>
      )}

      {(state.status === "detected" ||
        state.status === "analyzing" ||
        state.status === "error") && (
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

          {state.status === "error" && <p className="spendly-error">{state.message}</p>}
        </div>
      )}

      {state.status === "result" && (
        <div className="spendly-result">
          <RecommendationCard
            recommendation={state.result.recommendation}
            confidence={state.result.confidence}
            reasoning={state.result.reasoning}
            summary={state.result.summary}
          />
          <SpendingSummary budgetImpact={state.result.personal_insights.budget_impact} />
          <SimilarProducts purchases={state.result.personal_insights.similar_purchases} />
          <PriceComparisonCard comparison={state.result.price_comparison} />
          <button
            className="spendly-analyze-btn spendly-secondary"
            onClick={() => setState({ status: "detected", product: state.product })}
          >
            Back
          </button>
        </div>
      )}
    </div>
  );
}
