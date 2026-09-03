from dataclasses import dataclass
from datetime import datetime

from sources.base.source_result import SourceProduct


@dataclass
class NormalizedPrice:
    base_price: float
    currency: str
    discount: float
    shipping_cost: float | None  # None means unknown — never treated as 0
    final_price: float  # base_price - discount, excluding unknown shipping
    shipping_cost_known: bool
    availability: bool
    timestamp: datetime


def normalize_price(source_product: SourceProduct) -> NormalizedPrice:
    discount = source_product.discount or 0.0
    final_price = round(source_product.base_price - discount, 2)

    return NormalizedPrice(
        base_price=source_product.base_price,
        currency=source_product.currency,
        discount=discount,
        shipping_cost=source_product.shipping_cost,
        final_price=final_price,
        shipping_cost_known=source_product.shipping_cost is not None,
        availability=source_product.availability,
        timestamp=source_product.last_checked_at,
    )
