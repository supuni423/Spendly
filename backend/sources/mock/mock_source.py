import json
import re
from datetime import datetime, timezone
from pathlib import Path

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


# Five independent synthetic stores (2 clothing, 3 electronics), all
# defined in catalog.json — the single source of truth also read by
# extension/scripts/generate-test-pages.mjs to build the matching
# browsable demo pages, so the storefronts you click through and the
# prices this pipeline actually computes can never drift apart. Every
# clothing product is listed at both clothing stores, and every
# electronics product at all three electronics stores, at different
# prices, so every demo product has genuine cross-store spread.

_CATALOG_PATH = Path(__file__).parent / "catalog.json"
_catalog = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))


def _build_store_catalog(store_key: str) -> list[dict]:
    shipping_cost = _catalog["stores"][store_key]["shipping_cost"]
    rows = []
    for product in _catalog["products"]:
        price = product["prices"].get(store_key)
        if price is None:
            continue
        rows.append(
            _item(
                f"{store_key}-{product['sku']}".upper(),
                product["name"],
                brand=product.get("brand"),
                category=product.get("category"),
                sku=product["sku"],
                attributes=product.get("attributes"),
                base_price=float(price),
                shipping_cost=shipping_cost,
            )
        )
    return rows


_STORE_INSTANCES: dict[str, MockStoreSource] = {
    store_key: MockStoreSource(store_key, _build_store_catalog(store_key))
    for store_key in _catalog["stores"]
}

StyleHubSource = _STORE_INSTANCES["stylehub"]
TrendCartSource = _STORE_INSTANCES["trendcart"]
TechMartSource = _STORE_INSTANCES["techmart"]
QuickBuySource = _STORE_INSTANCES["quickbuy"]
ByteBazaarSource = _STORE_INSTANCES["bytebazaar"]

ALL_MOCK_STORES: list[MockStoreSource] = list(_STORE_INSTANCES.values())
