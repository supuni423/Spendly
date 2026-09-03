from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from models.user import User
from schemas.product import SavedProductCreate, SavedProductRead
from services.product_service import (
    list_saved_products,
    save_product,
    to_saved_product_read,
    unsave_product,
)

router = APIRouter(prefix="/api/saved-products", tags=["saved-products"])


@router.post("", response_model=SavedProductRead, status_code=status.HTTP_201_CREATED)
def save(
    data: SavedProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SavedProductRead:
    saved = save_product(db, current_user.id, data.product)
    return to_saved_product_read(db, saved)


@router.get("", response_model=list[SavedProductRead])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SavedProductRead]:
    saved = list_saved_products(db, current_user.id)
    return [to_saved_product_read(db, s) for s in saved]


@router.delete("/{saved_product_id}", status_code=status.HTTP_204_NO_CONTENT)
def unsave(
    saved_product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    removed = unsave_product(db, current_user.id, saved_product_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Saved product not found"
        )
