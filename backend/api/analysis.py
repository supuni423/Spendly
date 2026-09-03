from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from core.rate_limit import rate_limit
from models.user import User
from schemas.analysis import AnalysisResponse, AnalyzeRequest
from services.shopping_agent import analyze_product

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# Each analysis triggers an LLM call (real cost/quota) plus a market-source
# lookup — worth its own, more conservative budget than a typical read endpoint.
analysis_rate_limit = rate_limit("analysis", max_requests=20, window_seconds=60)


@router.post("", response_model=AnalysisResponse, dependencies=[Depends(analysis_rate_limit)])
def analyze(
    request: AnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisResponse:
    return analyze_product(db, current_user.id, request)
