def _login_and_get_token(client) -> str:
    resp = client.post(
        "/auth/login",
        data={"username": "admin", "password": "admin1234"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]

def test_login_admin(client):
    token = _login_and_get_token(client)
    assert token and isinstance(token, str)

def test_user_crud_flow(client):
    token = _login_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "username": "alice",
        "full_name": "Alice Doe",
        "email": "alice@example.com",
        "password": "alice1234"
    }
    r = client.post("/users", json=payload, headers=headers)
    assert r.status_code in (200, 201), r.text
    created = r.json()
    user_id = created["id"]
    assert created["username"] == "alice"

    r = client.get("/users", headers=headers)
    assert r.status_code == 200, r.text
    users = r.json()
    assert any(u["username"] == "alice" for u in users)

    r = client.put(f"/users/{user_id}", json={"full_name": "Alice Updated"}, headers=headers)
    assert r.status_code == 200, r.text
    updated = r.json()
    assert updated["full_name"] == "Alice Updated"

    r = client.delete(f"/users/{user_id}", headers=headers)
    assert r.status_code in (200, 204), r.text

    r = client.get("/users", headers=headers)
    assert r.status_code == 200
    assert not any(u["id"] == user_id for u in r.json())