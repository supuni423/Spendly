export type MatchType = "EXACT_MATCH" | "HIGH_CONFIDENCE_MATCH" | "SIMILAR_PRODUCT" | "NO_MATCH";

export interface CurrentProductInput {
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

export interface PriceComparisonMatch {
  source: string;
  name: string;
  price: number;
  currency: string;
  match_type: MatchType;
  match_confidence: number;
  savings: number | null;
  savings_percentage: number | null;
  shipping_cost_known: boolean;
  availability: boolean;
  product_url: string | null;
}

export interface PriceComparisonResult {
  current_product: CurrentProductInput;
  matches: PriceComparisonMatch[];
  lowest_price: number | null;
  potential_savings: number | null;
  checked_at: string;
}
