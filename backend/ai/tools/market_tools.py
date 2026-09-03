from ai.tools.context import ToolContext
from ai.tools.price_tools import get_or_compute_comparison
from models.market_product import MarketProduct
from schemas.price_comparison import MatchType
from services.market.market_service import get_price_history as _get_price_history

CHECK_MARKET_AVAILABILITY_DECLARATION = {
    "name": "check_market_availability",
    "description": (
        "Checks whether any confirmed same-product match found by compare_prices is actually "
        "in stock right now."
    ),
    "parameters": {"type": "object", "properties": {}},
}

GET_PRICE_HISTORY_DECLARATION = {
    "name": "get_price_history",
    "description": (
        "Returns the recorded price history for the best-matching listing of the current "
        "product, so you can mention whether its price has recently dropped or risen."
    ),
    "parameters": {"type": "object", "properties": {}},
}


def check_market_availability(context: ToolContext) -> dict:
    result = get_or_compute_comparison(context)
    same_product_matches = [
        m for m in result.matches if m.match_type in (MatchType.EXACT_MATCH, MatchType.HIGH_CONFIDENCE_MATCH)
    ]
    return {
        "any_match_found": len(same_product_matches) > 0,
        "any_available": any(m.availability for m in same_product_matches),
    }


def get_price_history(context: ToolContext) -> list[dict]:
    result = get_or_compute_comparison(context)
    same_product_matches = [
        m for m in result.matches if m.match_type in (MatchType.EXACT_MATCH, MatchType.HIGH_CONFIDENCE_MATCH)
    ]
    if not same_product_matches:
        return []

    best = min(same_product_matches, key=lambda m: m.price)
    market_product = context.db.query(MarketProduct).filter(
        MarketProduct.source == best.source, MarketProduct.name == best.name
    ).first()
    if market_product is None:
        return []

    history = _get_price_history(context.db, market_product.id)
    return [{"price": h.price, "currency": h.currency, "recorded_at": h.recorded_at.isoformat()} for h in history]
