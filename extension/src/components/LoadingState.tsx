export function LoadingState({ label }: { label: string }) {
  return (
    <div className="spendly-loading">
      <div className="spendly-spinner" />
      <p>{label}</p>
    </div>
  );
}
