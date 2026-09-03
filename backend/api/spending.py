from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.spending import SpendingSummary
from services.spending_service import get_spending_summary

router = APIRouter(prefix="/api/spending", tags=["spending"])


@router.get("", response_model=SpendingSummary)
def summary(
    month: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SpendingSummary:
    target = None
    if month is not None:
        try:
            year_str, month_str = month.split("-")
            target = date(int(year_str), int(month_str), 1)
        except (ValueError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="month must be formatted YYYY-MM",
            ) from exc

    return get_spending_summary(db, current_user.id, target)
