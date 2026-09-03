import type { BudgetImpact } from "@/types/analysis";
import { formatPrice } from "@/utils/priceFormatting";

export function SpendingSummary({ budgetImpact }: { budgetImpact: BudgetImpact }) {
  const { currency, current_month_total, projected_total, normal_monthly_average, percent_above_average } =
    budgetImpact;

  return (
    <div className="spendly-section">
      <h3>Spending impact</h3>
      <div className="spendly-spending-row">
        <span>This month so far</span>
        <span>{formatPrice(current_month_total, currency)}</span>
      </div>
      <div className="spendly-spending-row">
        <span>With this purchase</span>
        <span>{formatPrice(projected_total, currency)}</span>
      </div>
      <div className="spendly-spending-row">
        <span>Your normal average</span>
        <span>{formatPrice(normal_monthly_average, currency)}</span>
      </div>
      {percent_above_average !== null && (
        <p className={`spendly-budget-note ${percent_above_average > 0 ? "spendly-over" : "spendly-under"}`}>
          {percent_above_average > 0
            ? `${percent_above_average.toFixed(0)}% above your normal monthly spending`
            : `${Math.abs(percent_above_average).toFixed(0)}% below your normal monthly spending`}
        </p>
      )}
    </div>
  );
}
