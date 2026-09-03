from datetime import datetime, timezone

from schemas.price_comparison import CurrentProductInput, MatchType
from services.price.price_comparison_service import compare_prices
from services.price.savings_service import calculate_savings
from sources.base.source_result import SourceProduct


def _source(**overrides) -> SourceProduct:
    defaults = dict(
        source="mock",
        source_product_id="X-1",
        name="Black Floral Dress",
        brand=None,
        category=None,
        description=None,
        sku=None,
        model_number=None,
        attributes={},
        base_price=3900.0,
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


# --- savings_service ---


def test_calculate_savings_positive():
    savings, pct = calculate_savings(4500, 3900)
    assert savings == 600
    assert pct == 13.33


def test_calculate_savings_when_alternative_is_not_cheaper():
    savings, pct = calculate_savings(4500, 4500)
    assert savings is None and pct is None

    savings, pct = calculate_savings(4500, 5000)
    assert savings is None and pct is None


def test_calculate_savings_with_zero_current_price_is_undefined():
    savings, pct = calculate_savings(0, 100)
    assert savings is None and pct is None


# --- compare_prices ---


def test_lowest_price_and_potential_savings_from_matches():
    candidate = CurrentProductInput(product_name="Black Floral Dress", price=4500, currency="LKR")
    sources = [
        _source(source_product_id="A", name="Black Floral Dress", base_price=3900),
        _source(source_product_id="B", name="Black Floral Dress", base_price=4100),
    ]

    result = compare_prices(candidate, sources)

    assert result.lowest_price == 3900.0
    assert result.potential_savings == 600.0
    assert len(result.matches) == 2


def test_missing_price_source_is_excluded_gracefully():
    # A source with no usable price data shouldn't crash the pipeline —
    # SourceProduct requires base_price, so "missing" is modeled as an
    # unavailable listing instead.
    candidate = CurrentProductInput(product_name="Black Floral Dress", price=4500)
    sources = [_source(source_product_id="A", availability=False, base_price=3000)]

    result = compare_prices(candidate, sources)

    assert result.matches[0].savings is None  # unavailable listings aren't sold as savings
    assert result.lowest_price is None


def test_duplicate_source_listings_are_both_returned_and_sorted():
    candidate = CurrentProductInput(product_name="Black Floral Dress", price=4500)
    sources = [
        _source(source_product_id="A", base_price=4000),
        _source(source_product_id="A", base_price=4000),
    ]

    result = compare_prices(candidate, sources)

    assert len(result.matches) == 2
    assert result.matches[0].price == result.matches[1].price == 4000.0


def test_no_match_sources_are_excluded_from_results():
    candidate = CurrentProductInput(product_name="Black Floral Dress", price=4500)
    sources = [_source(source_product_id="A", name="Totally Unrelated Widget", base_price=10)]

    result = compare_prices(candidate, sources)

    assert result.matches == []
    assert result.lowest_price is None
    assert result.potential_savings is None


def test_similar_product_is_shown_without_savings_claim():
    candidate = CurrentProductInput(
        product_name="Air Max 90 Red", brand="Nike", category="Shoes", price=15000,
        attributes={"color": "red"},
    )
    sources = [
        _source(
            source_product_id="A",
            name="Air Max 90 Blue",
            brand="Nike",
            category="Shoes",
            base_price=9000,
            attributes={"color": "blue"},
        )
    ]

    result = compare_prices(candidate, sources)

    assert result.matches[0].match_type == MatchType.SIMILAR_PRODUCT
    assert result.matches[0].savings is None
    assert result.lowest_price is None
