def _auth_headers(client, email="insights@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _buy(client, headers, name, category, price, purchase_date):
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
            "quantity": 1,
            "purchase_date": purchase_date,
        },
    )


def test_budget_impact_reflects_normal_average(client):
    headers = _auth_headers(client)
    _buy(client, headers, "Item A", "Misc", 4000, "2026-06-01")
    _buy(client, headers, "Item B", "Misc", 6000, "2026-07-01")

    response = client.post(
        "/api/insights",
        headers=headers,
        json={"name": "New Item", "category": "Misc", "price": 9000},
    )

    impact = response.json()["budget_impact"]
    assert impact["normal_monthly_average"] == 5000.0
    assert impact["projected_total"] == 9000.0
    assert impact["percent_above_average"] == 80.0  # (9000-5000)/5000 * 100


def test_budget_impact_with_no_history_has_no_percentage(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/insights",
        headers=headers,
        json={"name": "First Ever Item", "category": "Misc", "price": 3000},
    )

    impact = response.json()["budget_impact"]
    assert impact["normal_monthly_average"] == 0.0
    assert impact["percent_above_average"] is None


def test_purchase_frequency_counts_and_averages_gaps(client):
    headers = _auth_headers(client)
    _buy(client, headers, "Dress 1", "Dresses", 4000, "2026-05-01")
    _buy(client, headers, "Dress 2", "Dresses", 4500, "2026-06-01")  # +31 days
    _buy(client, headers, "Dress 3", "Dresses", 5000, "2026-06-21")  # +20 days

    response = client.post(
        "/api/insights",
        headers=headers,
        json={"name": "Dress 4", "category": "Dresses", "price": 4800},
    )

    frequency = response.json()["purchase_frequency"]
    assert frequency["purchase_count"] == 3
    assert frequency["average_days_between_purchases"] == 25.5


def test_purchase_frequency_for_unseen_category_is_zero(client):
    headers = _auth_headers(client)

    response = client.post(
        "/api/insights",
        headers=headers,
        json={"name": "Item", "category": "Brand New Category", "price": 1000},
    )

    frequency = response.json()["purchase_frequency"]
    assert frequency["purchase_count"] == 0
    assert frequency["average_days_between_purchases"] is None
