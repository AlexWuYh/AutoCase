"""User management endpoint tests."""
from __future__ import annotations


def test_list_users_requires_admin(client, regular_user, user_headers):
    resp = client.get("/api/v1/users", headers=user_headers)
    assert resp.status_code == 403


def test_list_users_as_admin(client, admin_user, regular_user, admin_headers):
    resp = client.get("/api/v1/users", headers=admin_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert {u["username"] for u in body["items"]} == {"admin", "alice"}


def test_create_user_as_admin(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/users",
        json={
            "username": "bob",
            "email": "bob@test.com",
            "password": "bobpass123",
            "role": "user",
            "is_active": True,
        },
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["username"] == "bob"


def test_create_user_duplicate(client, admin_user, regular_user, admin_headers):
    resp = client.post(
        "/api/v1/users",
        json={
            "username": "alice",
            "email": "different@x.com",
            "password": "xxx123",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 409


def test_create_user_short_password(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/users",
        json={
            "username": "tiny",
            "email": "tiny@x.com",
            "password": "123",
        },
        headers=admin_headers,
    )
    assert resp.status_code == 422


def test_update_user_disable(client, admin_user, regular_user, admin_headers):
    resp = client.put(
        f"/api/v1/users/{regular_user.id}",
        json={"is_active": False},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False


def test_cannot_demote_last_admin(client, admin_user, admin_headers):
    resp = client.put(
        f"/api/v1/users/{admin_user.id}",
        json={"role": "user"},
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "last active admin" in resp.json()["detail"]


def test_delete_user(client, admin_user, regular_user, admin_headers):
    resp = client.delete(
        f"/api/v1/users/{regular_user.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 200


def test_cannot_delete_self(client, admin_user, admin_headers):
    resp = client.delete(
        f"/api/v1/users/{admin_user.id}",
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert "yourself" in resp.json()["detail"]


def test_reset_password(client, admin_user, regular_user, admin_headers):
    resp = client.post(
        f"/api/v1/users/{regular_user.id}/reset-password",
        json={"new_password": "brand-new-pass"},
        headers=admin_headers,
    )
    assert resp.status_code == 200

    login = client.post(
        "/api/v1/auth/login",
        json={"username": "alice", "password": "brand-new-pass"},
    )
    assert login.status_code == 200
