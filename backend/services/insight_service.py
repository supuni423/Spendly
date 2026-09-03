from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.purchase import Purchase
from schemas.insight import CandidateProduct, PersonalInsights, PurchaseFrequency
from services.similarity_service import find_similar_purchases
from services.spending_service import calculate_budget_impact


def get_purchase_frequency(db: Session, user_id: int, category: str | None) -> PurchaseFrequency:
    query = select(Purchase.purchase_date).where(Purchase.user_id == user_id)

    if category is not None:
        category_row = db.scalar(select(Category).where(Category.name == category))
        if category_row is None:
            return PurchaseFrequency(
                category=category,
                purchase_count=0,
                first_purchase_date=None,
                last_purchase_date=None,
                average_days_between_purchases=None,
            )
        query = query.where(Purchase.category_id == category_row.id)

    dates = sorted(db.scalars(query))

    average_gap = None
    if len(dates) >= 2:
        gaps = [(dates[i] - dates[i - 1]).days for i in range(1, len(dates))]
        average_gap = round(sum(gaps) / len(gaps), 1)

    return PurchaseFrequency(
        category=category,
        purchase_count=len(dates),
        first_purchase_date=dates[0] if dates else None,
        last_purchase_date=dates[-1] if dates else None,
        average_days_between_purchases=average_gap,
    )


def get_personal_insights(
    db: Session, user_id: int, candidate: CandidateProduct
) -> PersonalInsights:
    similar_purchases = find_similar_purchases(db, user_id, candidate)
    budget_impact = calculate_budget_impact(db, user_id, candidate.price)
    purchase_frequency = get_purchase_frequency(db, user_id, candidate.category)

    return PersonalInsights(
        similar_purchases=similar_purchases,
        similar_purchase_count=len(similar_purchases),
        budget_impact=budget_impact,
        purchase_frequency=purchase_frequency,
    )
