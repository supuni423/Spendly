from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PriceComparison(Base):
    __tablename__ = "price_comparisons"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    lowest_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    highest_price: Mapped[float | None] = mapped_column(Numeric(12, 2))
    current_price: Mapped[float] = mapped_column(Numeric(12, 2))
    potential_savings: Mapped[float | None] = mapped_column(Numeric(12, 2))
    comparison_currency: Mapped[str] = mapped_column(String(3), default="LKR")
