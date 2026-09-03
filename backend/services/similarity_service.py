import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.category import Category
from models.product import Product
from models.purchase import Purchase
from schemas.insight import CandidateProduct, SimilarPurchase

CATEGORY_WEIGHT = 0.5
BRAND_WEIGHT = 0.3
NAME_WEIGHT = 0.2
SIMILARITY_THRESHOLD = 0.5

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str | None) -> set[str]:
    if not text:
        return set()
    return set(_TOKEN_RE.findall(text.lower()))


def _name_similarity(a: str, b: str) -> float:
    tokens_a, tokens_b = _tokens(a), _tokens(b)
    if not tokens_a or not tokens_b:
        return 0.0
    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return len(intersection) / len(union)


def _score(
    candidate: CandidateProduct, product_name: str, brand: str | None, category: str | None
) -> float:
    category_match = (
        1.0
        if candidate.category and category and candidate.category.lower() == category.lower()
        else 0.0
    )
    brand_match = (
        1.0 if candidate.brand and brand and candidate.brand.lower() == brand.lower() else 0.0
    )
    name_score = _name_similarity(candidate.name, product_name)

    return (
        category_match * CATEGORY_WEIGHT + brand_match * BRAND_WEIGHT + name_score * NAME_WEIGHT
    )


def find_similar_purchases(
    db: Session, user_id: int, candidate: CandidateProduct, limit: int = 10
) -> list[SimilarPurchase]:
    rows = db.execute(
        select(Purchase, Product, Category.name)
        .join(Product, Purchase.product_id == Product.id)
        .outerjoin(Category, Product.category_id == Category.id)
        .where(Purchase.user_id == user_id)
    ).all()

    matches: list[SimilarPurchase] = []
    for purchase, product, category_name in rows:
        score = _score(candidate, product.name, product.brand, category_name)
        if score < SIMILARITY_THRESHOLD:
            continue
        matches.append(
            SimilarPurchase(
                product_name=product.name,
                brand=product.brand,
                category=category_name,
                purchase_date=purchase.purchase_date,
                purchase_price=float(purchase.purchase_price),
                similarity_score=round(score, 3),
            )
        )

    matches.sort(key=lambda m: (m.similarity_score, m.purchase_date), reverse=True)
    return matches[:limit]
