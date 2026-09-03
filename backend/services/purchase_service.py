from sqlalchemy import select
from sqlalchemy.orm import Session

from models.product import Product
from models.purchase import Purchase
from schemas.purchase import PurchaseCreate, PurchaseRead
from services.product_service import get_or_create_product, to_product_read


def create_purchase(db: Session, user_id: int, data: PurchaseCreate) -> Purchase:
    product = get_or_create_product(db, data.product)

    purchase = Purchase(
        user_id=user_id,
        product_id=product.id,
        purchase_price=data.purchase_price,
        quantity=data.quantity,
        purchase_date=data.purchase_date,
        category_id=product.category_id,
        condition=data.condition,
    )
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


def list_purchases(db: Session, user_id: int) -> list[Purchase]:
    return list(
        db.scalars(
            select(Purchase)
            .where(Purchase.user_id == user_id)
            .order_by(Purchase.purchase_date.desc())
        )
    )


def get_purchase(db: Session, user_id: int, purchase_id: int) -> Purchase | None:
    return db.scalar(
        select(Purchase).where(Purchase.id == purchase_id, Purchase.user_id == user_id)
    )


def to_purchase_read(db: Session, purchase: Purchase) -> PurchaseRead:
    product = db.get(Product, purchase.product_id)
    return PurchaseRead(
        id=purchase.id,
        product=to_product_read(db, product),
        purchase_price=float(purchase.purchase_price),
        quantity=purchase.quantity,
        purchase_date=purchase.purchase_date,
        condition=purchase.condition,
    )
