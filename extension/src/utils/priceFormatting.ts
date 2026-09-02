const CURRENCY_SYMBOLS: Record<string, string> = {
  LKR: "Rs. ",
  USD: "$",
  EUR: "€",
  GBP: "£",
};

export function formatPrice(amount: number, currency: string): string {
  const symbol = CURRENCY_SYMBOLS[currency] ?? `${currency} `;
  return `${symbol}${amount.toLocaleString(undefined, { maximumFractionDigits: 2 })}`;
}
