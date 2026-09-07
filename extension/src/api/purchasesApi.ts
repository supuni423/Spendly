import { apiClient } from "./apiClient";
import type { DetectedProduct } from "@/types/product";

function todayIsoDate(): string {
  return new Date().toISOString().slice(0, 10);
}

export function toPurchaseCreateRequest(product: DetectedProduct, purchasePrice: number) {
  return {
    product: {
      name: product.productName,
      brand: product.brand,
      category: product.category,
      description: product.description,
      price: product.price,
      currency: product.currency ?? "LKR",
      source: product.source,
      source_product_id: product.productId,
      product_url: product.productUrl,
      image_url: product.imageUrl,
    },
    purchase_price: purchasePrice,
    quantity: 1,
    purchase_date: todayIsoDate(),
  };
}

export function logPurchase(product: DetectedProduct, purchasePrice: number): Promise<unknown> {
  return apiClient.post("/api/purchases", toPurchaseCreateRequest(product, purchasePrice));
}
