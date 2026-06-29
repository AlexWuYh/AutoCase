"""Auth endpoint tests."""
from __future__ import annotations


def test_login_success(client, admin_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert body["expires_in"] > 0


def test_login_wrong_password(client, admin_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert resp.status_code == 401
    assert "Invalid" in resp.json()["detail"]


def test_login_unknown_user(client):
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "nobody", "password": "x"},
    )
    assert resp.status_code == 401


def test_login_inactive_user(client, db_session):
    from app.models.user import User, UserRole
    from app.security import hash_password
    user = User(
        username="ghost",
        email="g@x.com",
        password_hash=hash_password("x"),
        role=UserRole.USER,
        is_active=False,
    )
    db_session.add(user)
    db_session.commit()
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "ghost", "password": "x"},
    )
    assert resp.status_code == 403


def test_me_requires_token(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_returns_profile(client, admin_user, admin_headers):
    resp = client.get("/api/v1/auth/me", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["username"] == "admin"
    assert body["role"] == "admin"


def test_refresh_token(client, admin_user):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    refresh = login.json()["refresh_token"]
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_invalid_token(client):
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not-a-jwt"},
    )
    assert resp.status_code == 401


def test_change_password(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "admin123", "new_password": "newpass456"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    # Old password no longer works
    bad = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    assert bad.status_code == 401

    # New password works
    good = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "newpass456"},
    )
    assert good.status_code == 200


def test_change_password_wrong_old(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"old_password": "wrong", "new_password": "newpass456"},
        headers=admin_headers,
    )
    assert resp.status_code == 400
