import re
from datetime import datetime, timezone

from sources.base.product_source import ProductSource
from sources.base.source_result import SourceProduct

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _item(
    source_product_id: str,
    name: str,
    *,
    brand: str | None = None,
    category: str | None = None,
    sku: str | None = None,
    model_number: str | None = None,
    attributes: dict[str, str] | None = None,
    base_price: float,
    currency: str = "LKR",
    discount: float | None = None,
    shipping_cost: float | None = None,
) -> dict:
    return {
        "source_product_id": source_product_id,
        "name": name,
        "brand": brand,
        "category": category,
        "sku": sku,
        "model_number": model_number,
        "attributes": attributes or {},
        "base_price": base_price,
        "currency": currency,
        "discount": discount,
        "shipping_cost": shipping_cost,
    }


class MockStoreSource(ProductSource):
    """A synthetic store backed by a fixed catalog — no network calls, no
    external dependency. This is what the whole matching + comparison
    pipeline is built and tested against before any real, permitted source
    exists (Section 8). Several independent instances of this class (see
    the bottom of this file) stand in for several independent stores, so
    product_discovery_service genuinely aggregates across more than one
    source rather than trivially looping over a list of one.
    """

    def __init__(self, store_name: str, catalog: list[dict]):
        self._store_name = store_name
        self._catalog = catalog

    @property
    def name(self) -> str:
        return self._store_name

    def _to_source_product(self, row: dict) -> SourceProduct:
        return SourceProduct(
            source=self.name,
            source_product_id=row["source_product_id"],
            name=row["name"],
            brand=row["brand"],
            category=row["category"],
            description=None,
            sku=row["sku"],
            model_number=row["model_number"],
            attributes=row["attributes"],
            base_price=row["base_price"],
            currency=row["currency"],
            discount=row["discount"],
            shipping_cost=row["shipping_cost"],
            availability=True,
            product_url=f"https://{self._store_name}.mock.spendly.dev/products/{row['source_product_id']}",
            image_url=None,
            last_checked_at=datetime.now(timezone.utc),
        )

    def search_products(self, query: str, limit: int = 10) -> list[SourceProduct]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, dict]] = []
        for row in self._catalog:
            row_tokens = _tokens(f"{row['brand'] or ''} {row['name']}")
            overlap = len(query_tokens & row_tokens)
            if overlap == 0:
                continue
            scored.append((overlap / len(query_tokens | row_tokens), row))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [self._to_source_product(row) for _, row in scored[:limit]]

    def get_product(self, source_product_id: str) -> SourceProduct | None:
        row = next(
            (r for r in self._catalog if r["source_product_id"] == source_product_id), None
        )
        return self._to_source_product(row) if row else None

    def get_current_price(self, source_product_id: str) -> float | None:
        product = self.get_product(source_product_id)
        return product.base_price if product else None

    def check_availability(self, source_product_id: str) -> bool:
        return self.get_product(source_product_id) is not None


# Four independent synthetic stores. The same "Black Floral Dress" (SKU
# BFD-001) is deliberately priced differently at each fashion store so the
# price-comparison pipeline has real spread to demonstrate against.

TRENDCART_CATALOG = [
    _item(
        "TC-001",
        "Black Floral Dress",
        brand="Example",
        category="Dresses",
        sku="BFD-001",
        attributes={"color": "black", "size": "M"},
        base_price=4500.0,
        shipping_cost=300.0,
    ),
]

STYLEHUB_CATALOG = [
    _item(
        "SH-001",
        "Black Floral Dress",
        brand="Example",
        category="Dresses",
        sku="BFD-001",
        attributes={"color": "black", "size": "M"},
        base_price=4100.0,
        discount=200.0,  # final price 3900
        shipping_cost=250.0,
    ),
    _item(
        "SH-002",
        "Blue Floral Dress",
        brand="Example",
        category="Dresses",
        sku="BFD-002",
        attributes={"color": "blue", "size": "M"},
        base_price=3800.0,
        shipping_cost=250.0,
    ),
]

QUICKBUY_CATALOG = [
    _item(
        "QB-001",
        "Black Floral Dress",
        brand="Example",
        category="Dresses",
        sku="BFD-001",
        attributes={"color": "black", "size": "M"},
        base_price=4200.0,
        shipping_cost=None,  # shipping unknown from this listing
    ),
]

TECHMART_CATALOG = [
    _item(
        "TM-001",
        "Samsung Galaxy S25 256 GB Black",
        brand="Samsung",
        category="Phones",
        model_number="SM-S931B",
        attributes={"storage": "256GB", "color": "black"},
        base_price=289900.0,
        discount=5000.0,
        shipping_cost=0.0,
    ),
    _item(
        "TM-002",
        "Samsung Galaxy S25 Case",
        brand="Samsung",
        category="Phone Accessories",
        base_price=3500.0,
        shipping_cost=500.0,
    ),
]

TrendCartSource = MockStoreSource("trendcart", TRENDCART_CATALOG)
StyleHubSource = MockStoreSource("stylehub", STYLEHUB_CATALOG)
QuickBuySource = MockStoreSource("quickbuy", QUICKBUY_CATALOG)
TechMartSource = MockStoreSource("techmart", TECHMART_CATALOG)

ALL_MOCK_STORES: list[MockStoreSource] = [
    TrendCartSource,
    StyleHubSource,
    QuickBuySource,
    TechMartSource,
]
