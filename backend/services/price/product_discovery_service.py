from schemas.price_comparison import CurrentProductInput
from sources.base.product_source import ProductSource
from sources.base.source_result import SourceProduct
from sources.mock.mock_source import ALL_MOCK_STORES

# Every permitted source gets registered here (Section 8). Adding one never
# requires touching the matching engine, comparison service, or API layer.
REGISTERED_SOURCES: list[ProductSource] = list(ALL_MOCK_STORES)


def discover_candidates(
    candidate: CurrentProductInput, sources: list[ProductSource] | None = None
) -> list[SourceProduct]:
    active_sources = sources if sources is not None else REGISTERED_SOURCES

    results: list[SourceProduct] = []
    for source in active_sources:
        query = f"{candidate.brand or ''} {candidate.product_name}".strip()
        results.extend(source.search_products(query))
    return results
