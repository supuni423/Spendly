from datetime import datetime, timedelta, timezone

from jose import jwt

from app.config import get_settings

PRODUCT_PAYLOAD = {
    "name": "Black Floral Dress",
    "source": "store-a",
    "source_product_id": "SEC-001",
}


def _register(client, email="sec@example.com"):
    response = client.post(
        "/api/auth/register",
        json={"email": email, "password": "supersecret", "name": "Tester"},
    )
    return response.json()["access_token"]


def _expired_token(user_id: int) -> str:
    settings = get_settings()
    payload = {"sub": str(user_id), "exp": datetime.now(timezone.utc) - timedelta(minutes=1)}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


# --- Authorization: protected routes reject missing/invalid/expired tokens ---

PROTECTED_GET_ROUTES = ["/api/auth/me", "/api/purchases", "/api/saved-products", "/api/spending"]


def test_protected_routes_reject_missing_token(client):
    for route in PROTECTED_GET_ROUTES:
        response = client.get(route)
        assert response.status_code == 401, route


def test_protected_routes_reject_garbage_token(client):
    headers = {"Authorization": "Bearer not-a-real-token"}
    for route in PROTECTED_GET_ROUTES:
        response = client.get(route, headers=headers)
        assert response.status_code == 401, route


def test_protected_route_rejects_expired_token(client):
    token = _register(client, "expired@example.com")
    # Decode just to get the user id encoded in the valid token, then mint
    # an already-expired one for the same subject.
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    expired = _expired_token(int(payload["sub"]))

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired}"})
    assert response.status_code == 401


def test_protected_route_rejects_token_signed_with_wrong_secret(client):
    _register(client, "wrongsig@example.com")
    forged = jwt.encode({"sub": "1", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, "wrong-secret", algorithm="HS256")

    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


# --- IDOR / cross-user data isolation ---


def test_user_cannot_list_another_users_purchases(client):
    headers_a = {"Authorization": f"Bearer {_register(client, 'a@example.com')}"}
    headers_b = {"Authorization": f"Bearer {_register(client, 'b@example.com')}"}

    client.post(
        "/api/purchases",
        headers=headers_a,
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": 1000,
            "quantity": 1,
            "purchase_date": "2026-01-01",
        },
    )

    assert len(client.get("/api/purchases", headers=headers_a).json()) == 1
    assert len(client.get("/api/purchases", headers=headers_b).json()) == 0


def test_user_cannot_unsave_another_users_saved_product(client):
    headers_a = {"Authorization": f"Bearer {_register(client, 'saver@example.com')}"}
    headers_b = {"Authorization": f"Bearer {_register(client, 'attacker2@example.com')}"}

    saved = client.post(
        "/api/saved-products", headers=headers_a, json={"product": PRODUCT_PAYLOAD}
    ).json()

    response = client.delete(f"/api/saved-products/{saved['id']}", headers=headers_b)
    assert response.status_code == 404

    # Confirm it's genuinely untouched, not silently "succeeded" with a 404.
    still_there = client.get("/api/saved-products", headers=headers_a).json()
    assert any(s["id"] == saved["id"] for s in still_there)


def test_user_cannot_read_another_users_spending(client):
    headers_a = {"Authorization": f"Bearer {_register(client, 'spender@example.com')}"}
    headers_b = {"Authorization": f"Bearer {_register(client, 'nosy@example.com')}"}

    client.post(
        "/api/purchases",
        headers=headers_a,
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": 5000,
            "quantity": 1,
            "purchase_date": "2026-09-01",
        },
    )

    spending_b = client.get("/api/spending?month=2026-09", headers=headers_b).json()
    assert spending_b["total"] == 0


# --- Secret / sensitive-data exposure ---


def test_password_hash_never_appears_in_register_response(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "noleak@example.com", "password": "supersecret", "name": "Tester"},
    )
    assert "password" not in response.text.lower()
    assert "supersecret" not in response.text


def test_password_hash_never_appears_in_me_response(client):
    token = _register(client, "noleak2@example.com")
    response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert "password" not in response.text.lower()


# --- Input validation ---


def test_market_products_search_limit_is_bounded(client):
    token = _register(client, "bounds@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/api/market-products?limit=999999", headers=headers)
    assert response.status_code == 422  # rejected, not silently clamped-and-served


def test_register_rejects_short_password(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "shortpw@example.com", "password": "short", "name": "Tester"},
    )
    assert response.status_code == 422


def test_purchase_rejects_negative_price(client):
    token = _register(client, "negprice@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post(
        "/api/purchases",
        headers=headers,
        json={
            "product": PRODUCT_PAYLOAD,
            "purchase_price": -100,
            "quantity": 1,
            "purchase_date": "2026-01-01",
        },
    )
    assert response.status_code == 422


# --- Rate limiting ---


def test_login_is_rate_limited_after_repeated_attempts(client):
    _register(client, "ratelimited@example.com")

    responses = [
        client.post(
            "/api/auth/login",
            json={"email": "ratelimited@example.com", "password": "wrong-password"},
        )
        for _ in range(15)
    ]

    assert any(r.status_code == 429 for r in responses)
    assert all(r.status_code in (401, 429) for r in responses)
