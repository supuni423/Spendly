def _auth_headers(client, email="similarity@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _buy(client, headers, name, brand, category, price, purchase_date):
    client.post(
        "/api/purchases",
        headers=headers,
        json={
            "product": {
                "name": name,
                "brand": brand,
                "category": category,
                "source": "store-a",
                "source_product_id": f"{name}-{purchase_date}",
            },
            "purchase_price": price,
            "quantity": 1,
            "purchase_date": purchase_date,
        },
    )


def test_exact_category_and_brand_match_scores_high(client):
    headers = _auth_headers(client)
    _buy(client, headers, "Black Floral Dress", "Example", "Dresses", 4000, "2026-06-01")

    response = client.post(
        "/api/insights",
        headers=headers,
        json={"name": "Black Floral Dress", "brand": "Example", "category": "Dresses", "price": 4500},
    )

    body = response.json()
    assert body["similar_purchase_count"] == 1
    assert body["similar_purchases"][0]["similarity_score"] > 0.9


def test_unrelated_category_is_excluded(client):
    headers = _auth_headers(client)
    _buy(client, headers, "Bluetooth Speaker", "AudioCo", "Electronics", 6000, "2026-06-01")

    response = client.post(
        "/api/insights",
        headers=headers,
        json={"name": "Black Floral Dress", "brand": "Example", "category": "Dresses", "price": 4500},
    )

    body = response.json()
    assert body["similar_purchase_count"] == 0


def test_insights_requires_auth(client):
    response = client.post(
        "/api/insights", json={"name": "Dress", "category": "Dresses", "price": 4500}
    )
    assert response.status_code == 401
