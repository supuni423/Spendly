from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=500)
    brand: str | None = None
    category: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str = Field(default="LKR", min_length=3, max_length=3)
    source: str = Field(min_length=1, max_length=255)
    source_product_id: str | None = None
    product_url: str | None = None
    image_url: str | None = None


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    brand: str | None
    category: str | None = None
    description: str | None
    price: float | None
    currency: str
    source: str
    source_product_id: str | None
    product_url: str | None
    image_url: str | None
    created_at: datetime


class SavedProductCreate(BaseModel):
    product: ProductCreate


class SavedProductRead(BaseModel):
    id: int
    product: ProductRead
    saved_at: datetime
