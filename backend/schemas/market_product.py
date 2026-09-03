from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MarketProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    name: str
    brand: str | None
    category: str | None
    price: float
    currency: str
    product_url: str | None
    image_url: str | None
    availability: bool
    last_checked_at: datetime


class PriceHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    price: float
    currency: str
    recorded_at: datetime
