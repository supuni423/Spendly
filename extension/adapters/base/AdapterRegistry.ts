import type { ProductAdapter } from "./ProductAdapter";

/**
 * Adapters are checked in registration order; the first whose detect()
 * returns true wins. Register site-specific adapters before the generic
 * fallback so a permitted site's adapter takes priority over schema.org
 * parsing on the same page.
 */
export class AdapterRegistry {
  private adapters: ProductAdapter[] = [];

  register(adapter: ProductAdapter): void {
    this.adapters.push(adapter);
  }

  resolve(): ProductAdapter | null {
    for (const adapter of this.adapters) {
      if (adapter.detect()) {
        return adapter;
      }
    }
    return null;
  }
}
