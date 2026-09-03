from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.market_product import MarketProduct
from models.product import Product
from models.user import User
from schemas.market_product import MarketProductRead, PriceHistoryEntry
from services.market.alternative_product_service import get_alternatives
from services.market.market_service import get_price_history, search_market_products

router = APIRouter(prefix="/api/market-products", tags=["market-products"])
alternatives_router = APIRouter(prefix="/api/market-alternatives", tags=["market-products"])


@router.get("", response_model=list[MarketProductRead])
def search(
    query: str | None = None,
    category: str | None = None,
    brand: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[MarketProductRead]:
    results = search_market_products(db, query, category, brand, limit, offset)
    return [MarketProductRead.model_validate(r) for r in results]


@router.get("/{market_product_id}/price-history", response_model=list[PriceHistoryEntry])
def price_history(
    market_product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[PriceHistoryEntry]:
    market_product = db.get(MarketProduct, market_product_id)
    if market_product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Market product not found"
        )
    history = get_price_history(db, market_product_id)
    return [PriceHistoryEntry.model_validate(h) for h in history]


@alternatives_router.get("/{product_id}", response_model=list[MarketProductRead])
def alternatives(
    product_id: int,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[MarketProductRead]:
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    results = get_alternatives(db, product)
    return [MarketProductRead.model_validate(r) for r in results]
