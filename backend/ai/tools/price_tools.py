from ai.tools.context import ToolContext
from schemas.price_comparison import MatchType, PriceComparisonResult
from services.market.market_service import upsert_market_products
from services.price.price_comparison_service import compare_prices as _compare_prices
from services.price.product_discovery_service import discover_candidates
from services.price.savings_service import calculate_savings as _calculate_savings

COMPARE_PRICES_DECLARATION = {
    "name": "compare_prices",
    "description": (
        "Searches permitted external sources for the current product and returns every match "
        "found (same product at another store, or a similar-but-different product), each with "
        "its match type, price, and savings versus the current price. Also returns the overall "
        "lowest matching price and potential savings."
    ),
    "parameters": {"type": "object", "properties": {}},
}

FIND_SAME_PRODUCT_DECLARATION = {
    "name": "find_same_product",
    "description": (
        "Like compare_prices, but filtered to only listings confirmed to be the exact same "
        "product (or a high-confidence match) — never a merely similar item."
    ),
    "parameters": {"type": "object", "properties": {}},
}

FIND_SIMILAR_MARKET_PRODUCTS_DECLARATION = {
    "name": "find_similar_market_products",
    "description": (
        "Like compare_prices, but filtered to listings that are related but not the same "
        "product (e.g. a different color or size variant)."
    ),
    "parameters": {"type": "object", "properties": {}},
}

CALCULATE_SAVINGS_DECLARATION = {
    "name": "calculate_savings",
    "description": (
        "Calculates the exact savings amount and percentage between the current product's "
        "price and a specific alternative price you already know about."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "alternative_price": {
                "type": "number",
                "description": "The alternative price to compare against the current price.",
            }
        },
        "required": ["alternative_price"],
    },
}


def get_or_compute_comparison(context: ToolContext) -> PriceComparisonResult:
    if context._price_comparison_cache is None:
        source_products = discover_candidates(context.candidate)
        upsert_market_products(context.db, source_products)
        context._price_comparison_cache = _compare_prices(context.candidate, source_products)
    return context._price_comparison_cache


def compare_prices(context: ToolContext) -> dict:
    return get_or_compute_comparison(context).model_dump()


def find_same_product(context: ToolContext) -> list[dict]:
    result = get_or_compute_comparison(context)
    return [
        m.model_dump()
        for m in result.matches
        if m.match_type in (MatchType.EXACT_MATCH, MatchType.HIGH_CONFIDENCE_MATCH)
    ]


def find_similar_market_products(context: ToolContext) -> list[dict]:
    result = get_or_compute_comparison(context)
    return [m.model_dump() for m in result.matches if m.match_type == MatchType.SIMILAR_PRODUCT]


def calculate_savings(context: ToolContext, alternative_price: float) -> dict:
    savings, savings_percentage = _calculate_savings(context.candidate.price, alternative_price)
    return {"savings": savings, "savings_percentage": savings_percentage}
