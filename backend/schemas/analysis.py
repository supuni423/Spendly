from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from schemas.insight import PersonalInsights
from schemas.price_comparison import CurrentProductInput, PriceComparisonResult


class Recommendation(StrEnum):
    BUY = "BUY"
    CONSIDER = "CONSIDER"
    WAIT = "WAIT"


class AnalyzeRequest(CurrentProductInput):
    pass


class AnalysisResponse(BaseModel):
    recommendation: Recommendation
    confidence: float = Field(ge=0, le=1)
    reasoning: list[str]
    summary: str
    personal_insights: PersonalInsights
    price_comparison: PriceComparisonResult
    created_at: datetime
