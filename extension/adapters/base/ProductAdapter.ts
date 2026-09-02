import type { DetectedProduct } from "@/types/product";

export interface ProductAdapter {
  /** Name of the source/site this adapter handles, e.g. "generic", "store-a". */
  readonly source: string;

  /** Returns true if this adapter can extract a product from the current page. */
  detect(): boolean;

  /** Extracts the full product record. Only called after detect() returns true. */
  extractProduct(): DetectedProduct | null;

  getProductId(): string | null;
  getPrice(): { price: number | null; currency: string | null };
  getBrand(): string | null;
  getCategory(): string | null;
}
