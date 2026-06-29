"""LLM config + prompt endpoint tests."""
from __future__ import annotations


# ─── LLM Configs ────────────────────────────────────────────────────────

def test_list_llm_configs_empty(client, admin_user, admin_headers):
    resp = client.get("/api/v1/llm-configs", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_create_llm_config(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/llm-configs",
        json={"name": "Local Qwen", "model": "qwen2.5", "base_url": "http://x:8000/v1", "api_mode": "chat_completions", "allow_empty_key": True},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Local Qwen"
    assert body["is_default"] is False


def test_llm_config_is_default_mutual_exclusion(client, admin_user, admin_headers):
    c1 = client.post(
        "/api/v1/llm-configs",
        json={"name": "C1", "is_default": True, "model": "m1"},
        headers=admin_headers,
    )
    assert c1.status_code == 201
    assert c1.json()["is_default"] is True
    c2 = client.post(
        "/api/v1/llm-configs",
        json={"name": "C2", "is_default": True, "model": "m2"},
        headers=admin_headers,
    )
    assert c2.status_code == 201
    assert c2.json()["is_default"] is True
    # c1 should no longer be default
    g1 = client.get(f"/api/v1/llm-configs/{c1.json()['id']}", headers=admin_headers)
    assert g1.json()["is_default"] is False


def test_delete_default_config_blocked(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/llm-configs",
        json={"name": "Def", "is_default": True, "model": "m"},
        headers=admin_headers,
    )
    cid = resp.json()["id"]
    del_resp = client.delete(f"/api/v1/llm-configs/{cid}", headers=admin_headers)
    assert del_resp.status_code == 400
    assert "默认配置" in del_resp.json()["detail"]


def test_update_llm_config(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/llm-configs",
        json={"name": "X", "model": "m"},
        headers=admin_headers,
    )
    cid = resp.json()["id"]
    upd = client.put(
        f"/api/v1/llm-configs/{cid}",
        json={"name": "Y"},
        headers=admin_headers,
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Y"


def test_llm_config_test_connectivity(client, admin_user, admin_headers):
    """The test endpoint should at least respond (even if connection fails with error)."""
    resp = client.post(
        "/api/v1/llm-configs",
        json={"name": "Test", "model": "no-such-model", "base_url": "http://127.0.0.1:1/v1", "allow_empty_key": True, "api_mode": "chat_completions"},
        headers=admin_headers,
    )
    cid = resp.json()["id"]
    test = client.post(
        f"/api/v1/llm-configs/{cid}/test",
        json={"message": "echo"},
        headers=admin_headers,
    )
    assert test.status_code == 200
    body = test.json()
    assert "success" in body
    assert body["success"] is False  # localhost:1 isn't running
    assert body["elapsed_ms"] > 0


# ─── System Prompts ─────────────────────────────────────────────────────

def test_list_prompts_empty(client, admin_user, admin_headers):
    resp = client.get("/api/v1/system-prompts", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_create_prompt(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/system-prompts",
        json={"name": "Minimal", "content": "你是测试用例生成器。{}", "description": "minimal prompt"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["name"] == "Minimal"


def test_update_prompt(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/system-prompts",
        json={"name": "P", "content": "old", "is_default": False},
        headers=admin_headers,
    )
    pid = r.json()["id"]
    upd = client.put(
        f"/api/v1/system-prompts/{pid}",
        json={"content": "new"},
        headers=admin_headers,
    )
    assert upd.status_code == 200
    assert upd.json()["content"] == "new"


def test_delete_prompt(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/system-prompts",
        json={"name": "P", "content": "x"},
        headers=admin_headers,
    )
    pid = r.json()["id"]
    resp = client.delete(f"/api/v1/system-prompts/{pid}", headers=admin_headers)
    assert resp.status_code == 200


def test_prompt_default_mutual_exclusion(client, admin_user, admin_headers):
    c1 = client.post(
        "/api/v1/system-prompts",
        json={"name": "D1", "content": "a", "is_default": True},
        headers=admin_headers,
    )
    assert c1.json()["is_default"] is True
    c2 = client.post(
        "/api/v1/system-prompts",
        json={"name": "D2", "content": "b", "is_default": True},
        headers=admin_headers,
    )
    assert c2.json()["is_default"] is True
    g1 = client.get(f"/api/v1/system-prompts/{c1.json()['id']}", headers=admin_headers)
    assert g1.json()["is_default"] is False
