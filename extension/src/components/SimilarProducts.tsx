import type { SimilarPurchase } from "@/types/analysis";
import { formatPrice } from "@/utils/priceFormatting";
import { formatDate } from "@/utils/formatting";

export function SimilarProducts({ purchases }: { purchases: SimilarPurchase[] }) {
  if (purchases.length === 0) return null;

  return (
    <div className="spendly-section">
      <h3>
        Similar purchases <span className="spendly-muted">({purchases.length})</span>
      </h3>
      <ul className="spendly-similar-list">
        {purchases.map((p, i) => (
          <li key={i}>
            <span>{p.product_name}</span>
            <span className="spendly-muted">
              {formatPrice(p.purchase_price, "LKR")} · {formatDate(p.purchase_date)}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
