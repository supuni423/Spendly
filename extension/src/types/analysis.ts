import type { PriceComparisonResult } from "./priceComparison";

export type Recommendation = "BUY" | "CONSIDER" | "WAIT";

export interface SimilarPurchase {
  product_name: string;
  brand: string | null;
  category: string | null;
  purchase_date: string;
  purchase_price: number;
  similarity_score: number;
}

export interface BudgetImpact {
  currency: string;
  month: string;
  current_month_total: number;
  candidate_price: number;
  projected_total: number;
  normal_monthly_average: number;
  percent_above_average: number | null;
}

export interface PurchaseFrequency {
  category: string | null;
  purchase_count: number;
  first_purchase_date: string | null;
  last_purchase_date: string | null;
  average_days_between_purchases: number | null;
}

export interface PersonalInsights {
  similar_purchases: SimilarPurchase[];
  similar_purchase_count: number;
  budget_impact: BudgetImpact;
  purchase_frequency: PurchaseFrequency;
}

export interface AnalyzeRequest {
  product_name: string;
  brand: string | null;
  price: number;
  currency: string;
  category: string | null;
  product_url: string | null;
  sku: string | null;
  model_number: string | null;
  attributes: Record<string, string>;
}

export interface AnalysisResult {
  recommendation: Recommendation;
  confidence: number;
  reasoning: string[];
  summary: string;
  personal_insights: PersonalInsights;
  price_comparison: PriceComparisonResult;
  created_at: string;
}
