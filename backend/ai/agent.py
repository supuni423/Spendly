import json
import logging
from dataclasses import dataclass

from ai.prompts.shopping_agent_prompt import SYSTEM_INSTRUCTION, build_user_message
from ai.tools import market_tools, price_tools, purchase_tools, similarity_tools, spending_tools
from ai.tools.context import ToolContext
from services.llm_service import LLMClient, LLMNotConfiguredError, get_llm_client

logger = logging.getLogger(__name__)

MAX_ITERATIONS = 6

TOOLS: dict[str, tuple[dict, callable]] = {
    "get_purchase_history": (
        purchase_tools.GET_PURCHASE_HISTORY_DECLARATION,
        purchase_tools.get_purchase_history,
    ),
    "get_spending_summary": (
        spending_tools.GET_SPENDING_SUMMARY_DECLARATION,
        spending_tools.get_spending_summary,
    ),
    "calculate_budget_impact": (
        spending_tools.CALCULATE_BUDGET_IMPACT_DECLARATION,
        spending_tools.calculate_budget_impact,
    ),
    "find_similar_purchases": (
        similarity_tools.FIND_SIMILAR_PURCHASES_DECLARATION,
        similarity_tools.find_similar_purchases,
    ),
    "get_purchase_frequency": (
        similarity_tools.GET_PURCHASE_FREQUENCY_DECLARATION,
        similarity_tools.get_purchase_frequency,
    ),
    "compare_prices": (price_tools.COMPARE_PRICES_DECLARATION, price_tools.compare_prices),
    "find_same_product": (
        price_tools.FIND_SAME_PRODUCT_DECLARATION,
        price_tools.find_same_product,
    ),
    "find_similar_market_products": (
        price_tools.FIND_SIMILAR_MARKET_PRODUCTS_DECLARATION,
        price_tools.find_similar_market_products,
    ),
    "calculate_savings": (
        price_tools.CALCULATE_SAVINGS_DECLARATION,
        price_tools.calculate_savings,
    ),
    "check_market_availability": (
        market_tools.CHECK_MARKET_AVAILABILITY_DECLARATION,
        market_tools.check_market_availability,
    ),
    "get_price_history": (
        market_tools.GET_PRICE_HISTORY_DECLARATION,
        market_tools.get_price_history,
    ),
}


@dataclass
class AgentOutput:
    reasoning: list[str]
    summary: str
    used_fallback: bool


def _build_fallback(recommendation: str, fallback_facts: dict) -> AgentOutput:
    """Deterministic, template-based explanation used whenever no LLM key is
    configured or the live call fails — the feature must never break just
    because the LLM is unavailable.
    """
    insights = fallback_facts["personal_insights"]
    comparison = fallback_facts["price_comparison"]

    reasoning: list[str] = []

    similar_count = insights["similar_purchase_count"]
    if similar_count > 0:
        reasoning.append(f"You already purchased {similar_count} similar product(s).")

    budget = insights["budget_impact"]
    if budget["percent_above_average"] is not None and budget["percent_above_average"] > 0:
        reasoning.append(
            f"This purchase would put your monthly spending "
            f"{budget['percent_above_average']:.0f}% above your normal average."
        )

    if comparison["potential_savings"]:
        currency = comparison["current_product"]["currency"]
        reasoning.append(
            f"The same product is available elsewhere for "
            f"{currency} {comparison['potential_savings']:.2f} less."
        )

    if not reasoning:
        reasoning.append("No prior similar purchases, spending is within your normal range, and this is the best price found.")

    return AgentOutput(
        reasoning=reasoning,
        summary=f"Recommendation: {recommendation}.",
        used_fallback=True,
    )


def _extract_parts(response: dict) -> list[dict]:
    candidates = response.get("candidates") or []
    if not candidates:
        return []
    return candidates[0].get("content", {}).get("parts", [])


def _parse_final_answer(text: str) -> tuple[list[str], str] | None:
    cleaned = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        data = json.loads(cleaned)
        return list(data["reasoning"]), str(data["summary"])
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def run_agent(
    context: ToolContext,
    candidate_description: str,
    recommendation: str,
    fallback_facts: dict,
    llm_client: LLMClient | None = None,
) -> AgentOutput:
    try:
        client = llm_client or get_llm_client()
    except LLMNotConfiguredError:
        return _build_fallback(recommendation, fallback_facts)

    tools_payload = [{"functionDeclarations": [decl for decl, _ in TOOLS.values()]}]
    contents = [
        {"role": "user", "parts": [{"text": build_user_message(candidate_description, recommendation)}]}
    ]

    for _ in range(MAX_ITERATIONS):
        try:
            response = client.generate_content(
                system_instruction=SYSTEM_INSTRUCTION, contents=contents, tools=tools_payload
            )
        except Exception:
            logger.exception("LLM call failed; falling back to templated reasoning")
            return _build_fallback(recommendation, fallback_facts)

        parts = _extract_parts(response)
        function_calls = [p["functionCall"] for p in parts if "functionCall" in p]

        if not function_calls:
            text = "".join(p.get("text", "") for p in parts)
            parsed = _parse_final_answer(text)
            if parsed is None:
                logger.warning("LLM final response wasn't valid JSON; falling back")
                return _build_fallback(recommendation, fallback_facts)
            reasoning, summary = parsed
            return AgentOutput(reasoning=reasoning, summary=summary, used_fallback=False)

        # Replay the model's turn verbatim (not just the functionCall sub-dict) —
        # newer "thinking" models attach a thoughtSignature sibling field to each
        # part that MUST be echoed back on the next turn, or the API rejects the
        # request outright ("Function call is missing a thought_signature").
        contents.append({"role": "model", "parts": parts})

        response_parts = []
        for call in function_calls:
            name = call["name"]
            args = call.get("args") or {}
            if name not in TOOLS:
                result = {"error": f"unknown tool {name}"}
            else:
                try:
                    result = TOOLS[name][1](context, **args)
                except Exception as exc:  # noqa: BLE001
                    result = {"error": str(exc)}
            serialized = json.loads(json.dumps(result, default=str))
            # Gemini's functionResponse.response field is a Struct (JSON
            # object) — several tools return a bare list, which the API
            # rejects outright ("Proto field is not repeating, cannot
            # start list"), so wrap non-object results.
            if not isinstance(serialized, dict):
                serialized = {"results": serialized}

            function_response: dict = {"name": name, "response": serialized}
            if "id" in call:  # correlates parallel calls on newer models
                function_response["id"] = call["id"]
            response_parts.append({"functionResponse": function_response})
        contents.append({"role": "function", "parts": response_parts})

    logger.warning("Agent exceeded max iterations without a final answer; falling back")
    return _build_fallback(recommendation, fallback_facts)
