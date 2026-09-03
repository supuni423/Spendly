from sqlalchemy import select
from sqlalchemy.orm import Session

from models.market_product import MarketProduct
from models.price_history import PriceHistory
from sources.base.source_result import SourceProduct


def upsert_market_product(db: Session, source_product: SourceProduct) -> MarketProduct:
    existing = db.scalar(
        select(MarketProduct).where(
            MarketProduct.source == source_product.source,
            MarketProduct.source_product_id == source_product.source_product_id,
        )
    )

    final_price = round(source_product.base_price - (source_product.discount or 0.0), 2)

    if existing is None:
        record = MarketProduct(
            source=source_product.source,
            source_product_id=source_product.source_product_id,
            name=source_product.name,
            brand=source_product.brand,
            category=source_product.category,
            description=source_product.description,
            price=final_price,
            currency=source_product.currency,
            product_url=source_product.product_url,
            image_url=source_product.image_url,
            availability=source_product.availability,
            sku=source_product.sku,
            model_number=source_product.model_number,
            attributes=source_product.attributes,
            last_checked_at=source_product.last_checked_at,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        db.add(PriceHistory(market_product_id=record.id, price=final_price, currency=record.currency))
        db.commit()
        return record

    price_changed = float(existing.price) != final_price
    existing.price = final_price
    existing.availability = source_product.availability
    existing.last_checked_at = source_product.last_checked_at
    db.commit()
    db.refresh(existing)

    if price_changed:
        db.add(PriceHistory(market_product_id=existing.id, price=final_price, currency=existing.currency))
        db.commit()

    return existing


def upsert_market_products(
    db: Session, source_products: list[SourceProduct]
) -> list[MarketProduct]:
    return [upsert_market_product(db, sp) for sp in source_products]


def search_market_products(
    db: Session,
    query: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[MarketProduct]:
    stmt = select(MarketProduct)
    if query:
        stmt = stmt.where(MarketProduct.name.ilike(f"%{query}%"))
    if category:
        stmt = stmt.where(MarketProduct.category.ilike(category))
    if brand:
        stmt = stmt.where(MarketProduct.brand.ilike(brand))

    stmt = stmt.order_by(MarketProduct.name).offset(offset).limit(limit)
    return list(db.scalars(stmt))


def get_price_history(db: Session, market_product_id: int) -> list[PriceHistory]:
    return list(
        db.scalars(
            select(PriceHistory)
            .where(PriceHistory.market_product_id == market_product_id)
            .order_by(PriceHistory.recorded_at)
        )
    )
