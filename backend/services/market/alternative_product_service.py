from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.market_product import MarketProduct
from models.product import Product
from schemas.price_comparison import CurrentProductInput, MatchType
from services.price.product_matching_service import match_product
from sources.base.source_result import SourceProduct


def _market_product_to_source_product(market_product: MarketProduct) -> SourceProduct:
    return SourceProduct(
        source=market_product.source,
        source_product_id=market_product.source_product_id,
        name=market_product.name,
        brand=market_product.brand,
        category=market_product.category,
        description=market_product.description,
        sku=market_product.sku,
        model_number=market_product.model_number,
        attributes=market_product.attributes or {},
        base_price=float(market_product.price),
        currency=market_product.currency,
        discount=None,
        shipping_cost=None,
        availability=market_product.availability,
        product_url=market_product.product_url,
        image_url=market_product.image_url,
        last_checked_at=market_product.last_checked_at,
    )


def get_alternatives(db: Session, product: Product, limit: int = 10) -> list[MarketProduct]:
    category_name = None
    if product.category_id is not None:
        category = db.get(Category, product.category_id)
        category_name = category.name if category else None

    candidate = CurrentProductInput(
        product_name=product.name,
        brand=product.brand,
        price=float(product.price) if product.price is not None else 0.0,
        currency=product.currency,
        category=category_name,
    )

    market_products = list(db.scalars(select(MarketProduct)))

    alternatives: list[tuple[float, MarketProduct]] = []
    for market_product in market_products:
        source_product = _market_product_to_source_product(market_product)
        result = match_product(candidate, source_product)
        if result.match_type == MatchType.SIMILAR_PRODUCT:
            alternatives.append((result.confidence, market_product))

    alternatives.sort(key=lambda pair: pair[0], reverse=True)
    return [mp for _, mp in alternatives[:limit]]
