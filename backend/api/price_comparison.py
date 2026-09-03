from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.price_comparison import PriceComparison
from models.user import User
from schemas.price_comparison import CurrentProductInput, MatchType, PriceComparisonResult
from services.market.market_service import upsert_market_products
from services.price.price_comparison_service import compare_prices
from services.price.product_discovery_service import discover_candidates

router = APIRouter(prefix="/api/price-comparison", tags=["price-comparison"])


@router.post("", response_model=PriceComparisonResult)
def create_price_comparison(
    candidate: CurrentProductInput,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PriceComparisonResult:
    source_products = discover_candidates(candidate)
    upsert_market_products(db, source_products)

    result = compare_prices(candidate, source_products)

    matchable_prices = [
        m.price
        for m in result.matches
        if m.match_type in (MatchType.EXACT_MATCH, MatchType.HIGH_CONFIDENCE_MATCH)
    ]

    db.add(
        PriceComparison(
            user_id=current_user.id,
            product_id=None,
            lowest_price=result.lowest_price,
            highest_price=max(matchable_prices) if matchable_prices else None,
            current_price=candidate.price,
            potential_savings=result.potential_savings,
            comparison_currency=candidate.currency,
        )
    )
    db.commit()

    return result
