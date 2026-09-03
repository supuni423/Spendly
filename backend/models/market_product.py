from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MarketProduct(Base):
    __tablename__ = "market_products"
    __table_args__ = (
        UniqueConstraint("source", "source_product_id", name="uq_market_product_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    source: Mapped[str] = mapped_column(String(255), index=True)
    source_product_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(255), index=True)
    category: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(String)
    price: Mapped[float] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3), default="LKR")
    product_url: Mapped[str | None] = mapped_column(String(2048))
    image_url: Mapped[str | None] = mapped_column(String(2048))
    availability: Mapped[bool] = mapped_column(Boolean, default=True)
    sku: Mapped[str | None] = mapped_column(String(255), index=True)
    model_number: Mapped[str | None] = mapped_column(String(255), index=True)
    attributes: Mapped[dict] = mapped_column(JSON, default=dict)
    last_checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
