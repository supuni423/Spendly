import { AdapterRegistry } from "@adapters/base/AdapterRegistry";
import { GenericProductAdapter } from "@adapters/generic/GenericProductAdapter";
import type { DetectedProduct } from "@/types/product";

const registry = new AdapterRegistry();
registry.register(new GenericProductAdapter());

export function detectProduct(): DetectedProduct | null {
  const adapter = registry.resolve();
  if (!adapter) return null;
  return adapter.extractProduct();
}
