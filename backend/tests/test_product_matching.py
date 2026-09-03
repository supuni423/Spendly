from datetime import datetime, timezone

from schemas.price_comparison import CurrentProductInput, MatchType
from services.price.product_matching_service import match_product
from sources.base.source_result import SourceProduct


def _source(**overrides) -> SourceProduct:
    defaults = dict(
        source="mock",
        source_product_id="X-1",
        name="Black Floral Dress",
        brand="Example",
        category="Dresses",
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


def test_identical_titles_are_exact_match():
    candidate = CurrentProductInput(product_name="Black Floral Dress", price=4500)
    result = match_product(candidate, _source(name="Black Floral Dress"))
    assert result.match_type == MatchType.EXACT_MATCH


def test_titles_differing_only_by_formatting_are_exact_match():
    candidate = CurrentProductInput(product_name="Samsung Galaxy S25 256GB Black", price=289900)
    source = _source(name="Samsung Galaxy S25 256 GB Black", brand="Samsung", category="Phones")
    result = match_product(candidate, source)
    assert result.match_type == MatchType.EXACT_MATCH


def test_matching_sku_is_exact_match_even_with_different_title_wording():
    candidate = CurrentProductInput(product_name="Black Floral Dress (M)", price=4500, sku="BFD-001")
    source = _source(name="Black Floral Dress - Size M", sku="BFD-001")
    result = match_product(candidate, source)
    assert result.match_type == MatchType.EXACT_MATCH


def test_accessory_for_the_same_device_is_no_match():
    candidate = CurrentProductInput(
        product_name="Samsung Galaxy S25", brand="Samsung", category="Phones", price=289900
    )
    source = _source(
        name="Samsung Galaxy S25 Case",
        brand="Samsung",
        category="Phone Accessories",
        base_price=3500,
    )
    result = match_product(candidate, source)
    assert result.match_type == MatchType.NO_MATCH


def test_same_product_different_color_is_similar_not_exact():
    candidate = CurrentProductInput(
        product_name="Air Max 90 Red",
        brand="Nike",
        category="Shoes",
        price=15000,
        attributes={"color": "red", "size": "42"},
    )
    source = _source(
        name="Air Max 90 Blue",
        brand="Nike",
        category="Shoes",
        base_price=14500,
        attributes={"color": "blue", "size": "42"},
    )
    result = match_product(candidate, source)
    assert result.match_type == MatchType.SIMILAR_PRODUCT


def test_unrelated_products_are_no_match():
    candidate = CurrentProductInput(product_name="Black Floral Dress", price=4500)
    source = _source(
        name="Wireless Bluetooth Speaker", brand="AudioCo", category="Electronics", base_price=8900
    )
    result = match_product(candidate, source)
    assert result.match_type == MatchType.NO_MATCH


def test_high_confidence_when_brand_category_and_title_partially_align():
    candidate = CurrentProductInput(
        product_name="Classic Leather Wallet Brown", brand="Craft", category="Accessories", price=5000
    )
    source = _source(
        name="Classic Leather Wallet",
        brand="Craft",
        category="Accessories",
        base_price=4700,
    )
    result = match_product(candidate, source)
    assert result.match_type in (MatchType.HIGH_CONFIDENCE_MATCH, MatchType.EXACT_MATCH)
