from datetime import date

from ai.tools.context import ToolContext
from services.spending_service import calculate_budget_impact as _calculate_budget_impact
from services.spending_service import get_spending_summary as _get_spending_summary

GET_SPENDING_SUMMARY_DECLARATION = {
    "name": "get_spending_summary",
    "description": (
        "Returns the user's total spending for a given month, broken down by category, plus "
        "their normal monthly average (computed from all other months)."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "month": {
                "type": "string",
                "description": "Month to summarize, formatted YYYY-MM. Defaults to the current month.",
            }
        },
    },
}

CALCULATE_BUDGET_IMPACT_DECLARATION = {
    "name": "calculate_budget_impact",
    "description": (
        "Calculates how buying the current product would affect the user's spending this "
        "month: current total, projected total including this purchase, their normal monthly "
        "average, and the percentage above (or below) that average."
    ),
    "parameters": {"type": "object", "properties": {}},
}


def get_spending_summary(context: ToolContext, month: str | None = None) -> dict:
    target = None
    if month:
        year_str, month_str = month.split("-")
        target = date(int(year_str), int(month_str), 1)

    return _get_spending_summary(context.db, context.user_id, target).model_dump()


def calculate_budget_impact(context: ToolContext) -> dict:
    return _calculate_budget_impact(context.db, context.user_id, context.candidate.price).model_dump()
