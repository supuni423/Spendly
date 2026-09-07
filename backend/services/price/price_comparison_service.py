from datetime import datetime, timezone

from schemas.price_comparison import (
    CurrentProductInput,
    MatchType,
    PriceComparisonMatch,
    PriceComparisonResult,
)
from services.price.price_normalization_service import normalize_price
from services.price.product_discovery_service import discover_candidates
from services.price.product_matching_service import match_product
from services.price.savings_service import calculate_savings
from sources.base.source_result import SourceProduct

MATCHABLE_TYPES = {MatchType.EXACT_MATCH, MatchType.HIGH_CONFIDENCE_MATCH}


def compare_prices(
    candidate: CurrentProductInput, source_products: list[SourceProduct] | None = None
) -> PriceComparisonResult:
    """Deterministic price-comparison pipeline: discover -> match ->
    normalize -> compute savings. No LLM involvement anywhere here — every
    number in the result is backend-computed (Section 2's non-negotiable
    rule).
    """
    candidates = (
        source_products if source_products is not None else discover_candidates(candidate)
    )

    matches: list[PriceComparisonMatch] = []
    for source_product in candidates:
        match = match_product(candidate, source_product)
        if match.match_type == MatchType.NO_MATCH:
            continue

        # Only same-product matches (exact/high-confidence) are eligible
        # for a "you can buy this exact item cheaper elsewhere" savings
        # claim; a merely-similar product's price isn't comparable in
        # that sense, so it's surfaced with match info but no savings.
        # A currency mismatch (e.g. a real site showing a non-USD price)
        # is guarded the same way — the raw price/currency still shows
        # per store, but we never subtract across two different
        # currencies and present it as a real number.
        normalized = normalize_price(source_product)
        savings = savings_pct = None
        if (
            match.match_type in MATCHABLE_TYPES
            and normalized.availability
            and candidate.currency == normalized.currency
        ):
            savings, savings_pct = calculate_savings(candidate.price, normalized.final_price)

        matches.append(
            PriceComparisonMatch(
                source=source_product.source,
                name=source_product.name,
                price=normalized.final_price,
                currency=normalized.currency,
                match_type=match.match_type,
                match_confidence=match.confidence,
                savings=savings,
                savings_percentage=savings_pct,
                shipping_cost_known=normalized.shipping_cost_known,
                availability=normalized.availability,
                product_url=source_product.product_url,
            )
        )

    matches.sort(key=lambda m: m.price)

    matchable_prices = [
        m.price for m in matches if m.match_type in MATCHABLE_TYPES and m.savings is not None
    ]
    lowest_price = min(matchable_prices) if matchable_prices else None
    potential_savings = (
        round(candidate.price - lowest_price, 2) if lowest_price is not None else None
    )

    return PriceComparisonResult(
        current_product=candidate,
        matches=matches,
        lowest_price=lowest_price,
        potential_savings=potential_savings,
        checked_at=datetime.now(timezone.utc),
    )
