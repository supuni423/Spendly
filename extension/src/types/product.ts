export interface DetectedProduct {
  productName: string;
  brand: string | null;
  price: number | null;
  currency: string | null;
  category: string | null;
  description: string | null;
  imageUrl: string | null;
  productUrl: string;
  productId: string | null;
  sku: string | null;
  modelNumber: string | null;
  attributes: Record<string, string>;
  source: string;
}
