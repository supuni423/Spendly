import type { ProductAdapter } from "@adapters/base/ProductAdapter";
import type { DetectedProduct } from "@/types/product";

function getMeta(name: string): string | null {
  const el =
    document.querySelector(`meta[property="${name}"]`) ??
    document.querySelector(`meta[name="${name}"]`);
  return el?.getAttribute("content")?.trim() || null;
}

function getJsonLdProduct(): Record<string, unknown> | null {
  const scripts = document.querySelectorAll('script[type="application/ld+json"]');
  for (const script of scripts) {
    try {
      const data = JSON.parse(script.textContent ?? "");
      const items = Array.isArray(data) ? data : [data];
      for (const item of items) {
        const type = item["@type"];
        if (type === "Product" || (Array.isArray(type) && type.includes("Product"))) {
          return item as Record<string, unknown>;
        }
      }
    } catch {
      continue;
    }
  }
  return null;
}

function parsePrice(raw: string | null): number | null {
  if (!raw) return null;
  const cleaned = raw.replace(/[^0-9.]/g, "");
  const value = parseFloat(cleaned);
  return Number.isFinite(value) ? value : null;
}

/**
 * Fallback adapter for any page exposing schema.org Product JSON-LD or
 * Open Graph product tags. Used when no site-specific adapter matches.
 */
export class GenericProductAdapter implements ProductAdapter {
  readonly source = "generic";

  detect(): boolean {
    return getJsonLdProduct() !== null || getMeta("og:type") === "product";
  }

  extractProduct(): DetectedProduct | null {
    const jsonLd = getJsonLdProduct();

    const productName =
      (jsonLd?.name as string | undefined) ?? getMeta("og:title") ?? document.title;
    if (!productName) return null;

    const { price, currency } = this.getPrice();
    const brand = this.getBrand();

    return {
      productName,
      brand,
      price,
      currency,
      category: this.getCategory(),
      description:
        (jsonLd?.description as string | undefined) ?? getMeta("og:description"),
      imageUrl: (jsonLd?.image as string | undefined) ?? getMeta("og:image"),
      productUrl: getMeta("og:url") ?? window.location.href,
      productId: this.getProductId(),
      sku: (jsonLd?.sku as string | undefined) ?? null,
      modelNumber: (jsonLd?.mpn as string | undefined) ?? null,
      attributes: {},
      source: this.source,
    };
  }

  getProductId(): string | null {
    const jsonLd = getJsonLdProduct();
    return (jsonLd?.sku as string | undefined) ?? (jsonLd?.productID as string | undefined) ?? null;
  }

  getPrice(): { price: number | null; currency: string | null } {
    const jsonLd = getJsonLdProduct();
    const offers = jsonLd?.offers as Record<string, unknown> | undefined;
    const offer = Array.isArray(offers) ? offers[0] : offers;

    const price =
      parsePrice((offer?.price as string | number | undefined)?.toString() ?? null) ??
      parsePrice(getMeta("og:price:amount") ?? getMeta("product:price:amount"));
    const currency =
      (offer?.priceCurrency as string | undefined) ??
      getMeta("og:price:currency") ??
      getMeta("product:price:currency");

    return { price, currency };
  }

  getBrand(): string | null {
    const jsonLd = getJsonLdProduct();
    const brand = jsonLd?.brand as Record<string, unknown> | string | undefined;
    if (typeof brand === "string") return brand;
    if (brand && typeof brand === "object") return (brand.name as string) ?? null;
    return getMeta("product:brand");
  }

  getCategory(): string | null {
    const jsonLd = getJsonLdProduct();
    return (jsonLd?.category as string | undefined) ?? getMeta("product:category") ?? null;
  }
}
