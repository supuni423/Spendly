import type { PriceComparisonResult } from "@/types/priceComparison";
import { formatPrice } from "@/utils/priceFormatting";

const SAME_PRODUCT_TYPES = new Set(["EXACT_MATCH", "HIGH_CONFIDENCE_MATCH"]);

export function PriceComparisonCard({ comparison }: { comparison: PriceComparisonResult }) {
  const sameProduct = comparison.matches.filter((m) => SAME_PRODUCT_TYPES.has(m.match_type));
  const similar = comparison.matches.filter((m) => m.match_type === "SIMILAR_PRODUCT");

  if (sameProduct.length === 0 && similar.length === 0) {
    return (
      <div className="spendly-section">
        <h3>Price comparison</h3>
        <p className="spendly-muted">No matches found from Spendly's supported sources yet.</p>
      </div>
    );
  }

  return (
    <div className="spendly-section">
      <h3>Price comparison</h3>

      {sameProduct.length > 0 && (
        <div className="spendly-price-group">
          <p className="spendly-price-group-label">✓ Same product, other stores</p>
          {sameProduct.map((m, i) => (
            <div key={i} className="spendly-price-row">
              <div>
                <span className="spendly-store">{m.source}</span>
                {!m.availability && <span className="spendly-unavailable"> (unavailable)</span>}
                {!m.shipping_cost_known && (
                  <span className="spendly-muted"> · shipping cost unknown</span>
                )}
              </div>
              <div className="spendly-price-value">
                <span>{formatPrice(m.price, m.currency)}</span>
                {m.savings !== null && (
                  <span className="spendly-savings">
                    Save {formatPrice(m.savings, m.currency)} ({m.savings_percentage?.toFixed(0)}%)
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {similar.length > 0 && (
        <div className="spendly-price-group">
          <p className="spendly-price-group-label">Similar alternatives (different item)</p>
          {similar.map((m, i) => (
            <div key={i} className="spendly-price-row">
              <span>{m.name}</span>
              <span>{formatPrice(m.price, m.currency)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
