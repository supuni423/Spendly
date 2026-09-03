from datetime import datetime, timezone

from services.price.price_normalization_service import normalize_price
from sources.base.source_result import SourceProduct


def _source(**overrides) -> SourceProduct:
    defaults = dict(
        source="mock",
        source_product_id="X-1",
        name="Item",
        brand=None,
        category=None,
        description=None,
        sku=None,
        model_number=None,
        attributes={},
        base_price=1000.0,
        currency="LKR",
        discount=None,
        shipping_cost=None,
        availability=True,
        product_url=None,
        image_url=None,
        last_checked_at=datetime.now(timezone.utc),
    )
    defaults.update(overrides)
    return SourceProduct(**defaults)


def test_final_price_with_no_discount_or_shipping():
    normalized = normalize_price(_source(base_price=1000.0))
    assert normalized.final_price == 1000.0
    assert normalized.discount == 0.0


def test_final_price_subtracts_discount():
    normalized = normalize_price(_source(base_price=1000.0, discount=150.0))
    assert normalized.final_price == 850.0


def test_shipping_unknown_is_not_treated_as_zero():
    normalized = normalize_price(_source(base_price=1000.0, shipping_cost=None))
    assert normalized.shipping_cost is None
    assert normalized.shipping_cost_known is False
    # final_price never silently folds in a guessed shipping cost
    assert normalized.final_price == 1000.0


def test_known_shipping_cost_is_preserved_and_flagged_known():
    normalized = normalize_price(_source(base_price=1000.0, shipping_cost=250.0))
    assert normalized.shipping_cost == 250.0
    assert normalized.shipping_cost_known is True


def test_unavailable_product_is_flagged():
    normalized = normalize_price(_source(availability=False))
    assert normalized.availability is False


def test_invalid_negative_discount_still_produces_a_defined_final_price():
    # A discount larger than the base price is nonsensical input, but the
    # function must not raise or silently clamp — the caller decides what
    # to do with an unusual result.
    normalized = normalize_price(_source(base_price=100.0, discount=500.0))
    assert normalized.final_price == -400.0
