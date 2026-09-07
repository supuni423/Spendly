import pytest

from sources.mock.mock_source import ALL_MOCK_STORES, StyleHubSource, TrendCartSource

# --- Individual mock stores ---


def test_each_mock_store_has_a_distinct_name():
    names = [store.name for store in ALL_MOCK_STORES]
    assert len(names) == len(set(names)) == 5


def test_search_products_finds_relevant_catalog_entries():
    results = StyleHubSource.search_products("Black Floral Dress")
    assert any(r.name == "Black Floral Dress" for r in results)


def test_search_products_with_no_overlap_returns_empty():
    results = StyleHubSource.search_products("Completely Unrelated Query Term")
    assert results == []


def test_get_product_by_id_returns_normalized_shape():
    product = StyleHubSource.get_product("STYLEHUB-BFD-001")
    assert product is not None
    assert product.source == "stylehub"
    assert product.base_price > 0
    assert product.currency == "LKR"


def test_get_unknown_product_returns_none():
    assert StyleHubSource.get_product("DOES-NOT-EXIST") is None


def test_get_current_price_matches_catalog():
    assert StyleHubSource.get_current_price("STYLEHUB-BFD-001") == 3900.0
    assert StyleHubSource.get_current_price("DOES-NOT-EXIST") is None


def test_check_availability():
    assert StyleHubSource.check_availability("STYLEHUB-BFD-001") is True
    assert StyleHubSource.check_availability("DOES-NOT-EXIST") is False


def test_different_stores_price_the_same_sku_differently():
    trendcart_item = TrendCartSource.get_product("TRENDCART-BFD-001")
    stylehub_item = StyleHubSource.get_product("STYLEHUB-BFD-001")

    assert trendcart_item.sku == stylehub_item.sku == "BFD-001"
    assert trendcart_item.base_price != stylehub_item.base_price


@pytest.mark.parametrize("sku", ["BFD-001", "NAM90-001"])
def test_every_clothing_product_is_listed_at_both_clothing_stores(sku):
    listings = [
        store.get_current_price(row["source_product_id"])
        for store in ALL_MOCK_STORES
        for row in store._catalog
        if row["sku"] == sku
    ]
    assert len(listings) == 2
    assert len(set(listings)) == 2  # genuine price spread, not copy-pasted prices


@pytest.mark.parametrize("sku", ["SGS25-001", "DELL-INS15-001", "SONY-WHCH520-001"])
def test_every_electronics_product_is_listed_at_all_three_electronics_stores(sku):
    listings = [
        store.get_current_price(row["source_product_id"])
        for store in ALL_MOCK_STORES
        for row in store._catalog
        if row["sku"] == sku
    ]
    assert len(listings) == 3
    assert len(set(listings)) == 3


# --- API: price comparison + market products, end to end against the mock stores ---


def _auth_headers(client, email="market@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_price_comparison_aggregates_across_multiple_stores(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/price-comparison",
        headers=headers,
        json={
            "product_name": "Black Floral Dress",
            "brand": "Example",
            "price": 4500,
            "currency": "LKR",
            "category": "Dresses",
            "attributes": {"color": "black", "size": "M"},
        },
    )

    assert response.status_code == 200
    body = response.json()

    sources_seen = {m["source"] for m in body["matches"]}
    assert {"trendcart", "stylehub"}.issubset(sources_seen)

    assert body["lowest_price"] == 3900.0  # stylehub
    assert body["potential_savings"] == 600.0
    assert any(m["match_type"] == "EXACT_MATCH" for m in body["matches"])
    assert any(m["match_type"] == "SIMILAR_PRODUCT" for m in body["matches"])  # blue variant


def test_price_comparison_populates_market_products_catalog(client):
    headers = _auth_headers(client)

    client.post(
        "/api/price-comparison",
        headers=headers,
        json={"product_name": "Black Floral Dress", "price": 4500},
    )

    search = client.get("/api/market-products?query=Floral", headers=headers)
    assert search.status_code == 200
    names = [p["name"] for p in search.json()]
    assert "Black Floral Dress" in names


def test_price_history_endpoint_returns_entries(client):
    headers = _auth_headers(client)

    client.post(
        "/api/price-comparison",
        headers=headers,
        json={"product_name": "Black Floral Dress", "price": 4500},
    )
    market_products = client.get("/api/market-products?query=Floral", headers=headers).json()
    market_product_id = market_products[0]["id"]

    history = client.get(
        f"/api/market-products/{market_product_id}/price-history", headers=headers
    )

    assert history.status_code == 200
    assert len(history.json()) >= 1


def test_price_history_for_unknown_product_is_404(client):
    headers = _auth_headers(client)
    response = client.get("/api/market-products/999999/price-history", headers=headers)
    assert response.status_code == 404


def test_market_alternatives_for_unknown_product_is_404(client):
    headers = _auth_headers(client)
    response = client.get("/api/market-alternatives/999999", headers=headers)
    assert response.status_code == 404
