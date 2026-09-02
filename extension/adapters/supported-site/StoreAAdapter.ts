import type { ProductAdapter } from "@adapters/base/ProductAdapter";
import type { DetectedProduct } from "@/types/product";

/**
 * Template for the first permitted-site adapter (Section 8/12, Phase 6).
 * Not wired into the registry or manifest content_scripts yet — this file
 * exists as the pattern to copy once a real site is confirmed permitted.
 * Replace every selector below with the real site's markup before use.
 */
export class StoreAAdapter implements ProductAdapter {
  readonly source = "store-a";

  detect(): boolean {
    return window.location.hostname.endsWith("store-a.example.com");
  }

  extractProduct(): DetectedProduct | null {
    const productName = document.querySelector("[data-spendly-product-name]")?.textContent?.trim();
    if (!productName) return null;

    const { price, currency } = this.getPrice();

    return {
      productName,
      brand: this.getBrand(),
      price,
      currency,
      category: this.getCategory(),
      description: document.querySelector("[data-spendly-description]")?.textContent?.trim() ?? null,
      imageUrl: document.querySelector<HTMLImageElement>("[data-spendly-image]")?.src ?? null,
      productUrl: window.location.href,
      productId: this.getProductId(),
      sku: null,
      modelNumber: null,
      attributes: {},
      source: this.source,
    };
  }

  getProductId(): string | null {
    return document.querySelector("[data-spendly-product-id]")?.textContent?.trim() ?? null;
  }

  getPrice(): { price: number | null; currency: string | null } {
    const raw = document.querySelector("[data-spendly-price]")?.textContent ?? "";
    const value = parseFloat(raw.replace(/[^0-9.]/g, ""));
    return {
      price: Number.isFinite(value) ? value : null,
      currency: raw.includes("Rs.") ? "LKR" : null,
    };
  }

  getBrand(): string | null {
    return document.querySelector("[data-spendly-brand]")?.textContent?.trim() ?? null;
  }

  getCategory(): string | null {
    return document.querySelector("[data-spendly-category]")?.textContent?.trim() ?? null;
  }
}
