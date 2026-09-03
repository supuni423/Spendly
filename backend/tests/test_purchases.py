PRODUCT_PAYLOAD = {
    "name": "Black Floral Dress",
    "brand": "Example",
    "category": "Dresses",
    "price": 4500,
    "source": "store-a",
    "source_product_id": "BFD-001",
}


def _auth_headers(client, email="purchases@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_purchase_returns_purchase_with_product(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/purchases",
        headers=headers,
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": 4500,
            "quantity": 1,
            "purchase_date": "2026-08-15",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["product"]["name"] == "Black Floral Dress"
    assert body["purchase_price"] == 4500.0


def test_list_purchases_only_returns_own_purchases(client):
    headers_a = _auth_headers(client, "owner@example.com")
    headers_b = _auth_headers(client, "other@example.com")

    client.post(
        "/api/purchases",
        headers=headers_a,
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": 4500,
            "quantity": 1,
            "purchase_date": "2026-08-15",
        },
    )

    response_a = client.get("/api/purchases", headers=headers_a)
    response_b = client.get("/api/purchases", headers=headers_b)

    assert len(response_a.json()) == 1
    assert len(response_b.json()) == 0


def test_get_other_users_purchase_returns_404(client):
    headers_a = _auth_headers(client, "victim@example.com")
    headers_b = _auth_headers(client, "attacker@example.com")

    created = client.post(
        "/api/purchases",
        headers=headers_a,
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": 4500,
            "quantity": 1,
            "purchase_date": "2026-08-15",
        },
    )
    purchase_id = created.json()["id"]

    response = client.get(f"/api/purchases/{purchase_id}", headers=headers_b)

    assert response.status_code == 404


def test_create_purchase_requires_auth(client):
    response = client.post(
        "/api/purchases",
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": 4500,
            "quantity": 1,
            "purchase_date": "2026-08-15",
        },
    )
    assert response.status_code == 401
