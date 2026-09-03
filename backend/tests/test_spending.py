def _auth_headers(client, email="spending@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _buy(client, headers, name, category, price, purchase_date, quantity=1):
    client.post(
        "/api/purchases",
        headers=headers,
        json={
            "product": {
                "name": name,
                "category": category,
                "source": "store-a",
                "source_product_id": f"{name}-{purchase_date}",
            },
            "purchase_price": price,
            "quantity": quantity,
            "purchase_date": purchase_date,
        },
    )


def test_spending_summary_totals_current_month_by_category(client):
    headers = _auth_headers(client)
    _buy(client, headers, "Dress", "Clothing", 4500, "2026-08-05")
    _buy(client, headers, "Shoes", "Footwear", 3000, "2026-08-10")
    _buy(client, headers, "Bag", "Accessories", 1500, "2026-07-01")  # different month

    response = client.get("/api/spending?month=2026-08", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["month"] == "2026-08"
    assert body["total"] == 7500.0
    categories = {c["category"]: c["total"] for c in body["by_category"]}
    assert categories == {"Clothing": 4500.0, "Footwear": 3000.0}


def test_spending_summary_monthly_average_excludes_target_month(client):
    headers = _auth_headers(client)
    _buy(client, headers, "Dress", "Clothing", 4000, "2026-06-01")
    _buy(client, headers, "Shoes", "Footwear", 6000, "2026-07-01")
    _buy(client, headers, "Bag", "Accessories", 9000, "2026-08-01")

    response = client.get("/api/spending?month=2026-08", headers=headers)

    body = response.json()
    assert body["total"] == 9000.0
    assert body["monthly_average"] == 5000.0  # average of June (4000) and July (6000)


def test_spending_summary_with_no_purchases_is_zero(client):
    headers = _auth_headers(client)

    response = client.get("/api/spending?month=2026-08", headers=headers)

    body = response.json()
    assert body["total"] == 0
    assert body["monthly_average"] == 0
    assert body["by_category"] == []


def test_spending_summary_rejects_bad_month_format(client):
    headers = _auth_headers(client)

    response = client.get("/api/spending?month=not-a-month", headers=headers)

    assert response.status_code == 422
