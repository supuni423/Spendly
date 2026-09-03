from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.insight import CandidateProduct, PersonalInsights
from services.insight_service import get_personal_insights

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.post("", response_model=PersonalInsights)
def analyze_candidate(
    candidate: CandidateProduct,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PersonalInsights:
    return get_personal_insights(db, current_user.id, candidate)
