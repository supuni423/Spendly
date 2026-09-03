from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.purchase import PurchaseCreate, PurchaseRead
from services.purchase_service import (
    create_purchase,
    get_purchase,
    list_purchases,
    to_purchase_read,
)

router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@router.post("", response_model=PurchaseRead, status_code=status.HTTP_201_CREATED)
def create(
    data: PurchaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseRead:
    purchase = create_purchase(db, current_user.id, data)
    return to_purchase_read(db, purchase)


@router.get("", response_model=list[PurchaseRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[PurchaseRead]:
    purchases = list_purchases(db, current_user.id)
    return [to_purchase_read(db, p) for p in purchases]


@router.get("/{purchase_id}", response_model=PurchaseRead)
def get_one(
    purchase_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PurchaseRead:
    purchase = get_purchase(db, current_user.id, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found")
    return to_purchase_read(db, purchase)
