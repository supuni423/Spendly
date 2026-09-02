export type Recommendation = "BUY" | "CONSIDER" | "WAIT";

export interface AnalysisResult {
  recommendation: Recommendation;
  reasoning: string[];
  confidence: number;
  spendingImpact: {
    monthlySpending: number;
    normalAverage: number;
    percentAboveAverage: number;
  } | null;
  similarPurchaseCount: number;
  priceComparison: {
    lowestPrice: number | null;
    potentialSavings: number | null;
    currency: string;
  } | null;
}
