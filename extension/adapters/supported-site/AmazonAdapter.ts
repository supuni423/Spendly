import type { ProductAdapter } from "@adapters/base/ProductAdapter";
import type { DetectedProduct } from "@/types/product";

/**
 * Amazon doesn't expose schema.org Product JSON-LD or Open Graph product
 * tags on its product pages (confirmed by inspection — GenericProductAdapter
 * never matches there), so this reads Amazon's actual DOM instead. Amazon's
 * markup varies by category/A-B test and changes over time; this targets
 * the common product-page layout and degrades field-by-field (returning
 * null) rather than throwing when a selector doesn't match — only a
 * missing title fails detection entirely.
 */

const CURRENCY_PREFIXES: Array<[string, string]> = [
  ["LKR", "LKR"],
  ["$", "USD"],
  ["£", "GBP"],
  ["€", "EUR"],
];

function detectCurrency(raw: string): string | null {
  const trimmed = raw.trim();
  for (const [prefix, code] of CURRENCY_PREFIXES) {
    if (trimmed.startsWith(prefix)) return code;
  }
  return null;
}

function getMeta(property: string): string | null {
  return (
    document.querySelector(`meta[property="${property}"]`)?.getAttribute("content")?.trim() ??
    null
  );
}

export class AmazonAdapter implements ProductAdapter {
  readonly source = "amazon";

  detect(): boolean {
    return (
      window.location.hostname.includes("amazon.") &&
      document.querySelector("#productTitle") !== null
    );
  }

  extractProduct(): DetectedProduct | null {
    const productName = document.querySelector("#productTitle")?.textContent?.trim();
    if (!productName) return null;

    const { price, currency } = this.getPrice();

    return {
      productName,
      brand: this.getBrand(),
      price,
      currency,
      category: this.getCategory(),
      description: getMeta("og:description"),
      imageUrl:
        document.querySelector<HTMLImageElement>("#landingImage")?.src ??
        document.querySelector<HTMLImageElement>("#imgTagWrapperId img")?.src ??
        getMeta("og:image"),
      productUrl: window.location.href,
      productId: this.getProductId(),
      sku: this.getProductId(),
      modelNumber: null,
      attributes: {},
      source: this.source,
    };
  }

  getProductId(): string | null {
    const match = window.location.pathname.match(/\/(?:dp|gp\/product)\/([A-Z0-9]{10})/i);
    if (match) return match[1];
    return document.querySelector<HTMLInputElement>("#ASIN")?.value ?? null;
  }

  getPrice(): { price: number | null; currency: string | null } {
    const el =
      document.querySelector("#corePriceDisplay_desktop_feature_div .a-price .a-offscreen") ??
      document.querySelector("#apex_desktop .a-price .a-offscreen") ??
      document.querySelector(".a-price .a-offscreen");
    const raw = el?.textContent ?? "";
    if (!raw) return { price: null, currency: null };

    const value = parseFloat(raw.replace(/[^0-9.]/g, ""));
    return {
      price: Number.isFinite(value) ? value : null,
      currency: detectCurrency(raw),
    };
  }

  getBrand(): string | null {
    const raw = document.querySelector("#bylineInfo")?.textContent?.trim();
    if (!raw) return null;
    const cleaned = raw
      .replace(/^visit the\s+/i, "")
      .replace(/\s+store$/i, "")
      .replace(/^brand:\s*/i, "")
      .trim();
    return cleaned || null;
  }

  getCategory(): string | null {
    // Deliberately not read from Amazon's breadcrumb (e.g. "Fashion
    // Sneakers"). The matching algorithm's category-conflict rule
    // (product_matching_service.py) requires an exact string match against
    // the mock catalog's simple categories ("Shoes", "Phones", ...) — a
    // real, much more granular category would almost never equal that and
    // would force a hard NO_MATCH even on a genuinely strong brand/title
    // match. Returning null here lets title + brand carry the match
    // instead, which is what the catalog's categories were designed for.
    return null;
  }
}
