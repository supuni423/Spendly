from datetime import date

from pydantic import BaseModel, Field


class CandidateProduct(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    brand: str | None = None
    category: str | None = None
    price: float = Field(ge=0)


class SimilarPurchase(BaseModel):
    product_name: str
    brand: str | None
    category: str | None
    purchase_date: date
    purchase_price: float
    similarity_score: float


class BudgetImpact(BaseModel):
    currency: str
    month: str  # "YYYY-MM"
    current_month_total: float
    candidate_price: float
    projected_total: float
    normal_monthly_average: float
    percent_above_average: float | None  # None when there's no purchase history to compare against


class PurchaseFrequency(BaseModel):
    category: str | None
    purchase_count: int
    first_purchase_date: date | None
    last_purchase_date: date | None
    average_days_between_purchases: float | None


class PersonalInsights(BaseModel):
    similar_purchases: list[SimilarPurchase]
    similar_purchase_count: int
    budget_impact: BudgetImpact
    purchase_frequency: PurchaseFrequency
