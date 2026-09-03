from datetime import datetime

from pydantic import BaseModel, Field


class SourceProduct(BaseModel):
    """The normalized shape every ProductSource must return, regardless of
    what the underlying source's raw API/feed response looks like."""

    source: str
    source_product_id: str
    name: str
    brand: str | None = None
    category: str | None = None
    description: str | None = None
    sku: str | None = None
    model_number: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)

    base_price: float
    currency: str = "LKR"
    discount: float | None = None
    shipping_cost: float | None = None  # None means unknown, never assume 0
    availability: bool = True

    product_url: str | None = None
    image_url: str | None = None
    last_checked_at: datetime
