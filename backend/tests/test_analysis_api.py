def _auth_headers(client, email="analysis@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_analyze_with_no_history_recommends_buy(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/analysis",
        headers=headers,
        json={"product_name": "Brand New Gadget", "price": 1000},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["recommendation"] == "BUY"
    assert 0 <= body["confidence"] <= 1
    assert len(body["reasoning"]) >= 1
    assert body["personal_insights"]["similar_purchase_count"] == 0


def test_analyze_reproduces_spec_example_end_to_end(client):
    headers = _auth_headers(client)

    # Three prior similar purchases plus spending already above average
    for i, (price, month) in enumerate([(4000, "2026-06-01"), (4200, "2026-07-01"), (3800, "2026-08-01")]):
        client.post(
            "/api/purchases",
            headers=headers,
            json={
                "product": {
                    "name": f"Dress {i}",
                    "brand": "Example",
                    "category": "Dresses",
                    "source": "store-a",
                    "source_product_id": f"D-{i}",
                },
                "purchase_price": price,
                "quantity": 1,
                "purchase_date": month,
            },
        )

    response = client.post(
        "/api/analysis",
        headers=headers,
        json={
            "product_name": "Black Floral Dress",
            "brand": "Example",
            "price": 4500,
            "category": "Dresses",
            "attributes": {"color": "black"},
        },
    )

    body = response.json()
    assert body["recommendation"] in ("CONSIDER", "WAIT")
    assert body["price_comparison"]["lowest_price"] == 3900.0
    assert body["price_comparison"]["potential_savings"] == 600.0


def test_analyze_requires_auth(client):
    response = client.post("/api/analysis", json={"product_name": "Item", "price": 100})
    assert response.status_code == 401
