from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from schemas.product import ProductCreate, ProductRead


class PurchaseCreate(BaseModel):
    product: ProductCreate
    purchase_price: float = Field(ge=0)
    quantity: int = Field(default=1, ge=1)
    purchase_date: date
    condition: str | None = None


class PurchaseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product: ProductRead
    purchase_price: float
    quantity: int
    purchase_date: date
    condition: str | None
