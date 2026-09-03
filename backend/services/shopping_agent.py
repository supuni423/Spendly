from datetime import datetime, timezone

from sqlalchemy.orm import Session

from ai.agent import run_agent
from ai.tools.context import ToolContext
from ai.tools.price_tools import get_or_compute_comparison
from models.ai_analysis import AiAnalysis
from schemas.analysis import AnalysisResponse, Recommendation
from schemas.insight import CandidateProduct, PersonalInsights
from schemas.price_comparison import CurrentProductInput, MatchType, PriceComparisonResult
from services.insight_service import get_personal_insights
from services.llm_service import LLMClient

# Thresholds translate Section 11's "significant"/"moderate" language into
# concrete, testable numbers. Any single strong signal is enough to
# escalate the tier — matching the spec's "and/or" phrasing.
WAIT_SIMILAR_COUNT = 3
WAIT_BUDGET_PERCENT = 25.0
WAIT_SAVINGS_PERCENT = 15.0

CONSIDER_SIMILAR_COUNT = 1
CONSIDER_BUDGET_PERCENT = 0.0
CONSIDER_SAVINGS_PERCENT = 0.0

BASE_CONFIDENCE = 0.55
CONFIDENCE_PER_SIGNAL = 0.15
MAX_CONFIDENCE = 0.95


def _best_savings_percentage(price_comparison: PriceComparisonResult) -> float | None:
    matchable = [
        m.savings_percentage
        for m in price_comparison.matches
        if m.match_type in (MatchType.EXACT_MATCH, MatchType.HIGH_CONFIDENCE_MATCH)
        and m.savings_percentage is not None
    ]
    return max(matchable) if matchable else None


def decide_recommendation(
    personal_insights: PersonalInsights, price_comparison: PriceComparisonResult
) -> tuple[Recommendation, float]:
    """Every input here is a backend-computed fact (Phase 4 + Phase 5
    output) — this function, not the LLM, decides BUY/CONSIDER/WAIT and
    the confidence behind it. The agent only explains the result.
    """
    similar_count = personal_insights.similar_purchase_count
    budget_percent = personal_insights.budget_impact.percent_above_average
    savings_percent = _best_savings_percentage(price_comparison)

    if (
        similar_count >= WAIT_SIMILAR_COUNT
        or (budget_percent is not None and budget_percent >= WAIT_BUDGET_PERCENT)
        or (savings_percent is not None and savings_percent >= WAIT_SAVINGS_PERCENT)
    ):
        recommendation = Recommendation.WAIT
    elif (
        similar_count >= CONSIDER_SIMILAR_COUNT
        or (budget_percent is not None and budget_percent > CONSIDER_BUDGET_PERCENT)
        or (savings_percent is not None and savings_percent > CONSIDER_SAVINGS_PERCENT)
    ):
        recommendation = Recommendation.CONSIDER
    else:
        recommendation = Recommendation.BUY

    signals_available = 1  # similarity data is always available
    if budget_percent is not None:
        signals_available += 1
    if savings_percent is not None:
        signals_available += 1

    confidence = min(
        MAX_CONFIDENCE, round(BASE_CONFIDENCE + CONFIDENCE_PER_SIGNAL * signals_available, 2)
    )

    return recommendation, confidence


def analyze_product(
    db: Session,
    user_id: int,
    candidate: CurrentProductInput,
    llm_client: LLMClient | None = None,
) -> AnalysisResponse:
    candidate_product = CandidateProduct(
        name=candidate.product_name,
        brand=candidate.brand,
        category=candidate.category,
        price=candidate.price,
    )
    personal_insights = get_personal_insights(db, user_id, candidate_product)

    tool_context = ToolContext(db=db, user_id=user_id, candidate=candidate)
    price_comparison = get_or_compute_comparison(tool_context)

    recommendation, confidence = decide_recommendation(personal_insights, price_comparison)

    candidate_description = (
        f"{candidate.product_name}"
        + (f" by {candidate.brand}" if candidate.brand else "")
        + f", priced at {candidate.currency} {candidate.price}"
        + (f", category: {candidate.category}" if candidate.category else "")
    )

    agent_output = run_agent(
        tool_context,
        candidate_description=candidate_description,
        recommendation=recommendation.value,
        fallback_facts={
            "personal_insights": personal_insights.model_dump(),
            "price_comparison": price_comparison.model_dump(),
        },
        llm_client=llm_client,
    )

    created_at = datetime.now(timezone.utc)
    db.add(
        AiAnalysis(
            user_id=user_id,
            product_id=None,
            recommendation=recommendation.value,
            reasoning_summary=" ".join(agent_output.reasoning),
            confidence_score=confidence,
        )
    )
    db.commit()

    return AnalysisResponse(
        recommendation=recommendation,
        confidence=confidence,
        reasoning=agent_output.reasoning,
        summary=agent_output.summary,
        personal_insights=personal_insights,
        price_comparison=price_comparison,
        created_at=created_at,
    )
