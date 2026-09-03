export function formatPercent(value: number): string {
  return `${value > 0 ? "+" : ""}${value.toFixed(0)}%`;
}

export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}
