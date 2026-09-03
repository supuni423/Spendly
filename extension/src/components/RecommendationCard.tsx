import type { Recommendation } from "@/types/analysis";

const STYLES: Record<Recommendation, { label: string; emoji: string; className: string }> = {
  BUY: { label: "BUY", emoji: "✅", className: "spendly-rec-buy" },
  CONSIDER: { label: "CONSIDER", emoji: "🤔", className: "spendly-rec-consider" },
  WAIT: { label: "WAIT", emoji: "⏳", className: "spendly-rec-wait" },
};

interface Props {
  recommendation: Recommendation;
  confidence: number;
  reasoning: string[];
  summary: string;
}

export function RecommendationCard({ recommendation, confidence, reasoning, summary }: Props) {
  const style = STYLES[recommendation];

  return (
    <div className={`spendly-rec-card ${style.className}`}>
      <div className="spendly-rec-header">
        <span className="spendly-rec-badge">
          {style.emoji} {style.label}
        </span>
        <span className="spendly-rec-confidence">Confidence: {Math.round(confidence * 100)}%</span>
      </div>
      <p className="spendly-rec-summary">{summary}</p>
      <ul className="spendly-rec-reasoning">
        {reasoning.map((point, i) => (
          <li key={i}>{point}</li>
        ))}
      </ul>
    </div>
  );
}
