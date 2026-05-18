def test_register_and_login(client):
    r = client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    assert r.status_code == 200
    assert r.json()["email"] == "user@test.com"

def test_login_sets_cookie(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "pass123"
    })
    assert r.status_code == 200
    assert "access_token" in r.cookies

def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    r = client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "wrong"
    })
    assert r.status_code == 401

def test_me_returns_user(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com", "password": "pass123", "name": "Test"
    })
    client.post("/api/v1/auth/login", json={
        "email": "user@test.com", "password": "pass123"
    })
    r = client.get("/api/v1/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "user@test.com"
