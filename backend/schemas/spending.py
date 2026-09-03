from pydantic import BaseModel


class CategorySpending(BaseModel):
    category: str | None
    total: float


class SpendingSummary(BaseModel):
    currency: str
    month: str  # "YYYY-MM"
    total: float
    by_category: list[CategorySpending]
    monthly_average: float
