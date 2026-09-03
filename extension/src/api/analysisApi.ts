import { apiClient } from "./apiClient";
import type { AnalysisResult, AnalyzeRequest } from "@/types/analysis";
import type { DetectedProduct } from "@/types/product";

export function toAnalyzeRequest(product: DetectedProduct): AnalyzeRequest {
  return {
    product_name: product.productName,
    brand: product.brand,
    price: product.price ?? 0,
    currency: product.currency ?? "LKR",
    category: product.category,
    product_url: product.productUrl,
    sku: product.sku,
    model_number: product.modelNumber,
    attributes: product.attributes,
  };
}

export function analyzeProduct(product: DetectedProduct): Promise<AnalysisResult> {
  return apiClient.post<AnalysisResult>("/api/analysis", toAnalyzeRequest(product));
}
