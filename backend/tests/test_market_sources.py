from sources.mock.mock_source import MockSource

# --- MockSource itself ---


def test_search_products_finds_relevant_catalog_entries():
    source = MockSource()
    results = source.search_products("Black Floral Dress")
    assert any(r.name == "Black Floral Dress" for r in results)


def test_search_products_with_no_overlap_returns_empty():
    source = MockSource()
    results = source.search_products("Completely Unrelated Query Term")
    assert results == []


def test_get_product_by_id_returns_normalized_shape():
    source = MockSource()
    product = source.get_product("MOCK-001")
    assert product is not None
    assert product.source == "mock"
    assert product.base_price > 0
    assert product.currency == "LKR"


def test_get_unknown_product_returns_none():
    source = MockSource()
    assert source.get_product("DOES-NOT-EXIST") is None


def test_get_current_price_matches_catalog():
    source = MockSource()
    assert source.get_current_price("MOCK-001") == 3900.0
    assert source.get_current_price("DOES-NOT-EXIST") is None


def test_check_availability():
    source = MockSource()
    assert source.check_availability("MOCK-001") is True
    assert source.check_availability("DOES-NOT-EXIST") is False


# --- API: price comparison + market products, end to end against MockSource ---


def _auth_headers(client, email="market@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_price_comparison_endpoint_finds_cheaper_mock_listing(client):
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
    assert body["lowest_price"] == 3900.0
    assert body["potential_savings"] == 600.0
    assert any(m["match_type"] == "EXACT_MATCH" for m in body["matches"])


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
