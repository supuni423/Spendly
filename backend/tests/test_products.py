def _register_and_auth_headers(client, email="products@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_product_creates_category(client):
    headers = _register_and_auth_headers(client)

    response = client.post(
        "/api/products",
        headers=headers,
        json={
            "name": "Black Floral Dress",
            "brand": "Example",
            "category": "Dresses",
            "price": 4500,
            "currency": "LKR",
            "source": "store-a",
            "source_product_id": "BFD-001",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "Dresses"
    assert body["price"] == 4500.0


def test_create_product_dedupes_by_source_and_source_product_id(client):
    headers = _register_and_auth_headers(client)
    payload = {
        "name": "Black Floral Dress",
        "source": "store-a",
        "source_product_id": "BFD-001",
    }

    first = client.post("/api/products", headers=headers, json=payload)
    second = client.post("/api/products", headers=headers, json=payload)

    assert first.json()["id"] == second.json()["id"]


def test_get_unknown_product_returns_404(client):
    headers = _register_and_auth_headers(client)

    response = client.get("/api/products/999999", headers=headers)

    assert response.status_code == 404
