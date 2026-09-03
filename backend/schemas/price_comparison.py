from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class MatchType(StrEnum):
    EXACT_MATCH = "EXACT_MATCH"
    HIGH_CONFIDENCE_MATCH = "HIGH_CONFIDENCE_MATCH"
    SIMILAR_PRODUCT = "SIMILAR_PRODUCT"
    NO_MATCH = "NO_MATCH"


class CurrentProductInput(BaseModel):
    product_name: str = Field(min_length=1, max_length=500)
    brand: str | None = None
    price: float = Field(ge=0)
    currency: str = Field(default="LKR", min_length=3, max_length=3)
    category: str | None = None
    product_url: str | None = None
    sku: str | None = None
    model_number: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)


class PriceComparisonMatch(BaseModel):
    source: str
    name: str
    price: float  # final price: base - discount (+ shipping when known)
    currency: str
    match_type: MatchType
    match_confidence: float
    savings: float | None
    savings_percentage: float | None
    shipping_cost_known: bool
    product_url: str | None


class PriceComparisonResult(BaseModel):
    current_product: CurrentProductInput
    matches: list[PriceComparisonMatch]
    lowest_price: float | None
    potential_savings: float | None
    checked_at: datetime
