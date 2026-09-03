import re
from datetime import datetime, timezone

from sources.base.product_source import ProductSource
from sources.base.source_result import SourceProduct

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


# Synthetic catalog. Prices are intentionally lower than the "current
# product" prices used in tests/docs examples, so a Spendly analysis has
# something to recommend against. No network calls, no external dependency
# — this is what the whole matching + comparison pipeline is built and
# tested against before any real, permitted source exists (Section 8).
_CATALOG: list[dict] = [
    {
        "source_product_id": "MOCK-001",
        "name": "Black Floral Dress",
        "brand": "Example",
        "category": "Dresses",
        "sku": "BFD-001",
        "model_number": None,
        "attributes": {"color": "black", "size": "M"},
        "base_price": 3900.0,
        "currency": "LKR",
        "discount": None,
        "shipping_cost": 300.0,
        "product_url": "https://mock.spendly.dev/products/MOCK-001",
        "image_url": None,
    },
    {
        "source_product_id": "MOCK-002",
        "name": "Black Floral Dress",
        "brand": "Example",
        "category": "Dresses",
        "sku": "BFD-001",
        "model_number": None,
        "attributes": {"color": "black", "size": "M"},
        "base_price": 4100.0,
        "currency": "LKR",
        "discount": 200.0,
        "shipping_cost": None,  # shipping unknown from this listing
        "product_url": "https://mock.spendly.dev/products/MOCK-002",
        "image_url": None,
    },
    {
        "source_product_id": "MOCK-003",
        "name": "Blue Floral Dress",
        "brand": "Example",
        "category": "Dresses",
        "sku": "BFD-002",
        "model_number": None,
        "attributes": {"color": "blue", "size": "M"},
        "base_price": 3800.0,
        "currency": "LKR",
        "discount": None,
        "shipping_cost": 300.0,
        "product_url": "https://mock.spendly.dev/products/MOCK-003",
        "image_url": None,
    },
    {
        "source_product_id": "MOCK-004",
        "name": "Samsung Galaxy S25 256 GB Black",
        "brand": "Samsung",
        "category": "Phones",
        "sku": None,
        "model_number": "SM-S931B",
        "attributes": {"storage": "256GB", "color": "black"},
        "base_price": 289900.0,
        "currency": "LKR",
        "discount": 5000.0,
        "shipping_cost": 0.0,
        "product_url": "https://mock.spendly.dev/products/MOCK-004",
        "image_url": None,
    },
    {
        "source_product_id": "MOCK-005",
        "name": "Samsung Galaxy S25 Case",
        "brand": "Samsung",
        "category": "Phone Accessories",
        "sku": None,
        "model_number": None,
        "attributes": {},
        "base_price": 3500.0,
        "currency": "LKR",
        "discount": None,
        "shipping_cost": 500.0,
        "product_url": "https://mock.spendly.dev/products/MOCK-005",
        "image_url": None,
    },
]


class MockSource(ProductSource):
    @property
    def name(self) -> str:
        return "mock"

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
            product_url=row["product_url"],
            image_url=row["image_url"],
            last_checked_at=datetime.now(timezone.utc),
        )

    def search_products(self, query: str, limit: int = 10) -> list[SourceProduct]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return []

        scored: list[tuple[float, dict]] = []
        for row in _CATALOG:
            row_tokens = _tokens(f"{row['brand'] or ''} {row['name']}")
            overlap = len(query_tokens & row_tokens)
            if overlap == 0:
                continue
            scored.append((overlap / len(query_tokens | row_tokens), row))

        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [self._to_source_product(row) for _, row in scored[:limit]]

    def get_product(self, source_product_id: str) -> SourceProduct | None:
        row = next(
            (r for r in _CATALOG if r["source_product_id"] == source_product_id), None
        )
        return self._to_source_product(row) if row else None

    def get_current_price(self, source_product_id: str) -> float | None:
        product = self.get_product(source_product_id)
        return product.base_price if product else None

    def check_availability(self, source_product_id: str) -> bool:
        return self.get_product(source_product_id) is not None
