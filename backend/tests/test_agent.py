from datetime import datetime, timezone

from ai.agent import AgentOutput, run_agent
from ai.tools.context import ToolContext
from schemas.analysis import Recommendation
from schemas.insight import BudgetImpact, PersonalInsights, PurchaseFrequency
from schemas.price_comparison import (
    CurrentProductInput,
    MatchType,
    PriceComparisonMatch,
    PriceComparisonResult,
)
from services.shopping_agent import decide_recommendation

# --- decide_recommendation (deterministic, no DB / LLM involved) ---


def _insights(similar_count=0, percent_above_average=None) -> PersonalInsights:
    return PersonalInsights(
        similar_purchases=[],
        similar_purchase_count=similar_count,
        budget_impact=BudgetImpact(
            currency="LKR",
            month="2026-09",
            current_month_total=0,
            candidate_price=4500,
            projected_total=4500,
            normal_monthly_average=0,
            percent_above_average=percent_above_average,
        ),
        purchase_frequency=PurchaseFrequency(
            category="Dresses",
            purchase_count=similar_count,
            first_purchase_date=None,
            last_purchase_date=None,
            average_days_between_purchases=None,
        ),
    )


def _comparison(savings_percentage=None, match_type=MatchType.EXACT_MATCH) -> PriceComparisonResult:
    matches = []
    if savings_percentage is not None:
        matches.append(
            PriceComparisonMatch(
                source="mock",
                name="Item",
                price=100,
                currency="LKR",
                match_type=match_type,
                match_confidence=0.9,
                savings=1,
                savings_percentage=savings_percentage,
                shipping_cost_known=True,
                availability=True,
                product_url=None,
            )
        )
    return PriceComparisonResult(
        current_product=CurrentProductInput(product_name="Item", price=4500),
        matches=matches,
        lowest_price=100 if matches else None,
        potential_savings=1 if matches else None,
        checked_at=datetime.now(timezone.utc),
    )


def test_no_signals_is_buy():
    rec, confidence = decide_recommendation(_insights(), _comparison())
    assert rec == Recommendation.BUY
    assert confidence == 0.70  # only the always-available similarity signal


def test_one_similar_purchase_is_consider():
    rec, _ = decide_recommendation(_insights(similar_count=1), _comparison())
    assert rec == Recommendation.CONSIDER


def test_three_similar_purchases_is_wait():
    rec, _ = decide_recommendation(_insights(similar_count=3), _comparison())
    assert rec == Recommendation.WAIT


def test_high_budget_impact_alone_is_wait():
    rec, _ = decide_recommendation(_insights(percent_above_average=30), _comparison())
    assert rec == Recommendation.WAIT


def test_moderate_budget_impact_alone_is_consider():
    rec, _ = decide_recommendation(_insights(percent_above_average=10), _comparison())
    assert rec == Recommendation.CONSIDER


def test_big_savings_elsewhere_alone_is_wait():
    rec, _ = decide_recommendation(_insights(), _comparison(savings_percentage=20))
    assert rec == Recommendation.WAIT


def test_small_savings_elsewhere_alone_is_consider():
    rec, _ = decide_recommendation(_insights(), _comparison(savings_percentage=5))
    assert rec == Recommendation.CONSIDER


def test_similar_product_savings_dont_count_toward_recommendation():
    # A SIMILAR_PRODUCT match's "savings" (if any) is never a like-for-like
    # comparison, so it must not push the recommendation toward WAIT.
    rec, _ = decide_recommendation(
        _insights(), _comparison(savings_percentage=50, match_type=MatchType.SIMILAR_PRODUCT)
    )
    assert rec == Recommendation.BUY


def test_confidence_increases_with_more_available_signals():
    _, confidence_one_signal = decide_recommendation(_insights(), _comparison())
    _, confidence_two_signals = decide_recommendation(
        _insights(percent_above_average=10), _comparison()
    )
    _, confidence_three_signals = decide_recommendation(
        _insights(percent_above_average=10), _comparison(savings_percentage=5)
    )
    assert confidence_one_signal < confidence_two_signals < confidence_three_signals


# --- run_agent: fallback path (no LLM configured) ---


def _tool_context() -> ToolContext:
    return ToolContext(
        db=None,  # not touched by the fallback path
        user_id=1,
        candidate=CurrentProductInput(product_name="Black Floral Dress", price=4500),
    )


def _fallback_facts(similar_count=2, percent_above_average=28.0, potential_savings=600.0):
    return {
        "personal_insights": _insights(similar_count, percent_above_average).model_dump(),
        "price_comparison": {
            **_comparison().model_dump(),
            "potential_savings": potential_savings,
        },
    }


def test_run_agent_falls_back_when_no_llm_configured():
    output = run_agent(
        _tool_context(),
        candidate_description="Black Floral Dress, priced at LKR 4500",
        recommendation="CONSIDER",
        fallback_facts=_fallback_facts(),
        llm_client=None,
    )
    assert output.used_fallback is True
    assert len(output.reasoning) >= 1
    assert "2 similar" in output.reasoning[0]


# --- run_agent: scripted fake LLM client ---


class _FakeLLMClient:
    def __init__(self, responses: list[dict]):
        self._responses = responses
        self.calls = 0

    def generate_content(self, system_instruction, contents, tools):
        response = self._responses[self.calls]
        self.calls += 1
        return response


def _text_response(text: str) -> dict:
    return {"candidates": [{"content": {"role": "model", "parts": [{"text": text}]}}]}


def _function_call_response(name: str, args: dict | None = None) -> dict:
    return {
        "candidates": [
            {
                "content": {
                    "role": "model",
                    "parts": [{"functionCall": {"name": name, "args": args or {}}}],
                }
            }
        ]
    }


def test_run_agent_returns_final_json_answer_directly():
    client = _FakeLLMClient(
        [_text_response('{"reasoning": ["Fact one.", "Fact two."], "summary": "Consider it."}')]
    )

    output = run_agent(
        _tool_context(),
        candidate_description="desc",
        recommendation="CONSIDER",
        fallback_facts=_fallback_facts(),
        llm_client=client,
    )

    assert output.used_fallback is False
    assert output.reasoning == ["Fact one.", "Fact two."]
    assert output.summary == "Consider it."


def test_run_agent_executes_a_tool_call_then_returns_answer():
    client = _FakeLLMClient(
        [
            _function_call_response("find_similar_purchases"),
            _text_response('{"reasoning": ["Used a tool."], "summary": "Done."}'),
        ]
    )

    output = run_agent(
        _tool_context(),
        candidate_description="desc",
        recommendation="BUY",
        fallback_facts=_fallback_facts(),
        llm_client=client,
    )

    assert client.calls == 2
    assert output.used_fallback is False
    assert output.reasoning == ["Used a tool."]


def test_run_agent_falls_back_on_malformed_final_json():
    client = _FakeLLMClient([_text_response("not json at all")])

    output = run_agent(
        _tool_context(),
        candidate_description="desc",
        recommendation="BUY",
        fallback_facts=_fallback_facts(),
        llm_client=client,
    )

    assert output.used_fallback is True


def test_run_agent_falls_back_after_max_iterations():
    # The client always requests another tool call and never gives a final
    # answer — the agent must bail out rather than loop forever.
    infinite_calls = [_function_call_response("check_market_availability") for _ in range(10)]
    client = _FakeLLMClient(infinite_calls)

    output = run_agent(
        _tool_context(),
        candidate_description="desc",
        recommendation="BUY",
        fallback_facts=_fallback_facts(),
        llm_client=client,
    )

    assert output.used_fallback is True
    assert client.calls <= 6
