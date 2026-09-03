from ai.tools.context import ToolContext
from schemas.insight import CandidateProduct
from services.insight_service import get_purchase_frequency as _get_purchase_frequency
from services.similarity_service import find_similar_purchases as _find_similar_purchases

FIND_SIMILAR_PURCHASES_DECLARATION = {
    "name": "find_similar_purchases",
    "description": (
        "Finds past purchases similar to the current product, scored by category, brand, and "
        "title overlap. Use this to check whether the user already owns something like this."
    ),
    "parameters": {"type": "object", "properties": {}},
}

GET_PURCHASE_FREQUENCY_DECLARATION = {
    "name": "get_purchase_frequency",
    "description": (
        "Returns how often the user buys in a category: total count, first/last purchase date, "
        "and average days between purchases. Defaults to the current product's category."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "category": {
                "type": "string",
                "description": "Category to check. Defaults to the current product's category.",
            }
        },
    },
}


def _to_candidate_product(context: ToolContext) -> CandidateProduct:
    return CandidateProduct(
        name=context.candidate.product_name,
        brand=context.candidate.brand,
        category=context.candidate.category,
        price=context.candidate.price,
    )


def find_similar_purchases(context: ToolContext) -> list[dict]:
    matches = _find_similar_purchases(context.db, context.user_id, _to_candidate_product(context))
    return [m.model_dump() for m in matches]


def get_purchase_frequency(context: ToolContext, category: str | None = None) -> dict:
    resolved_category = category or context.candidate.category
    frequency = _get_purchase_frequency(context.db, context.user_id, resolved_category)
    return frequency.model_dump()
