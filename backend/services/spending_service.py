from collections import defaultdict
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.purchase import Purchase
from schemas.insight import BudgetImpact
from schemas.spending import CategorySpending, SpendingSummary


def _month_key(d: date) -> str:
    return f"{d.year:04d}-{d.month:02d}"


def _monthly_totals(db: Session, user_id: int) -> dict[str, float]:
    purchases = list(db.scalars(select(Purchase).where(Purchase.user_id == user_id)))
    totals: dict[str, float] = defaultdict(float)
    for purchase in purchases:
        totals[_month_key(purchase.purchase_date)] += float(purchase.purchase_price) * purchase.quantity
    return totals


def _monthly_average_excluding(totals_by_month: dict[str, float], target_key: str) -> float:
    other_totals = [total for key, total in totals_by_month.items() if key != target_key]
    return round(sum(other_totals) / len(other_totals), 2) if other_totals else 0.0


def get_spending_summary(db: Session, user_id: int, month: date | None = None) -> SpendingSummary:
    target = month or date.today()
    target_key = _month_key(target)

    purchases = list(db.scalars(select(Purchase).where(Purchase.user_id == user_id)))

    totals_by_month: dict[str, float] = defaultdict(float)
    category_totals_this_month: dict[int | None, float] = defaultdict(float)

    for purchase in purchases:
        line_total = float(purchase.purchase_price) * purchase.quantity
        key = _month_key(purchase.purchase_date)
        totals_by_month[key] += line_total
        if key == target_key:
            category_totals_this_month[purchase.category_id] += line_total

    category_ids = [cid for cid in category_totals_this_month if cid is not None]
    categories = {
        c.id: c.name for c in db.scalars(select(Category).where(Category.id.in_(category_ids)))
    } if category_ids else {}

    by_category = [
        CategorySpending(category=categories.get(cid), total=round(total, 2))
        for cid, total in sorted(category_totals_this_month.items(), key=lambda kv: -kv[1])
    ]

    return SpendingSummary(
        currency="LKR",
        month=target_key,
        total=round(totals_by_month.get(target_key, 0.0), 2),
        by_category=by_category,
        monthly_average=_monthly_average_excluding(totals_by_month, target_key),
    )


def calculate_budget_impact(
    db: Session, user_id: int, candidate_price: float, month: date | None = None
) -> BudgetImpact:
    target = month or date.today()
    target_key = _month_key(target)

    totals_by_month = _monthly_totals(db, user_id)
    current_month_total = round(totals_by_month.get(target_key, 0.0), 2)
    projected_total = round(current_month_total + candidate_price, 2)
    normal_average = _monthly_average_excluding(totals_by_month, target_key)

    percent_above_average = (
        round(((projected_total - normal_average) / normal_average) * 100, 2)
        if normal_average > 0
        else None
    )

    return BudgetImpact(
        currency="LKR",
        month=target_key,
        current_month_total=current_month_total,
        candidate_price=candidate_price,
        projected_total=projected_total,
        normal_monthly_average=normal_average,
        percent_above_average=percent_above_average,
    )
