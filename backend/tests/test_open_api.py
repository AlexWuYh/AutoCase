"""API Key management + Open API generation tests (mock LLM)."""
from __future__ import annotations

from unittest.mock import patch


# ─── API Key management ──────────────────────────────────────────────────

def test_create_and_list_api_key(client, admin_user, admin_headers):
    resp = client.post("/api/v1/api-keys", json={"name": "feishu-bot"}, headers=admin_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "feishu-bot"
    assert body["key"].startswith("ac_")  # plaintext returned once
    assert body["prefix"].startswith("ac_")

    lst = client.get("/api/v1/api-keys", headers=admin_headers)
    assert lst.status_code == 200
    items = lst.json()
    assert len(items) == 1
    assert "key" not in items[0]  # plaintext never listed


def test_revoke_api_key(client, admin_user, admin_headers):
    kid = client.post("/api/v1/api-keys", json={"name": "temp"}, headers=admin_headers).json()["id"]
    resp = client.delete(f"/api/v1/api-keys/{kid}", headers=admin_headers)
    assert resp.status_code == 200
    assert client.get("/api/v1/api-keys", headers=admin_headers).json() == []


def test_api_keys_require_auth(client):
    assert client.get("/api/v1/api-keys").status_code == 401


# ─── Open API auth ─────────────────────────────────────────────────────────

def test_open_generate_requires_api_key(client, admin_user):
    resp = client.post("/api/v1/open/generate", json={"cases": [{"module": "M", "feature": "F"}]})
    assert resp.status_code == 401


def test_open_generate_bad_key(client, admin_user):
    resp = client.post(
        "/api/v1/open/generate",
        json={"cases": [{"module": "M", "feature": "F"}]},
        headers={"X-API-Key": "ac_wrong"},
    )
    assert resp.status_code == 401


# ─── Open API generation (mock LLM) ──────────────────────────────────────

def _fake_items(spec):
    return [{"type": "功能测试", "name": "用例", "priority": "2", "pre": "无",
             "steps": ["步骤1"], "expected": ["期望1"], "stage": "功能测试阶段"}]


def _make_key(client, headers):
    return client.post("/api/v1/api-keys", json={"name": "k"}, headers=headers).json()["key"]


def _ensure_llm_config(client, headers):
    """The lifespan seed runs against the real engine, not the test's in-memory
    DB, so generation needs a config created through the API."""
    client.post(
        "/api/v1/llm-configs",
        json={"name": "test", "model": "m", "base_url": "http://x/v1",
              "allow_empty_key": True, "api_mode": "chat_completions", "is_default": True},
        headers=headers,
    )


def test_open_generate_sync_with_cases(client, admin_user, admin_headers):
    key = _make_key(client, admin_headers)
    _ensure_llm_config(client, admin_headers)
    with patch("autocase.llm_client.generate_llm_cases", side_effect=lambda spec, cfg, prompt: _fake_items(spec)), \
         patch("autocase.llm_client.generate_module_code", return_value="MOD"):
        resp = client.post(
            "/api/v1/open/generate",
            json={"cases": [
                {"module": "登录", "feature": "登录成功", "description": "正常登录", "keywords": ["登录"]},
            ]},
            headers={"X-API-Key": key},
        )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "success", body.get("error")
    assert body["total"] == 1
    assert len(body["cases"]) >= 1
    assert body["cases"][0]["case_id"]


def test_open_generate_sync_with_yaml_text(client, admin_user, admin_headers):
    key = _make_key(client, admin_headers)
    _ensure_llm_config(client, admin_headers)
    yaml_text = """cases:
  - module: 告警
    feature: 区域入侵
    description: 检测入侵
    keywords: [告警]
"""
    with patch("autocase.llm_client.generate_llm_cases", side_effect=lambda spec, cfg, prompt: _fake_items(spec)), \
         patch("autocase.llm_client.generate_module_code", return_value="ALM"):
        resp = client.post(
            "/api/v1/open/generate",
            json={"text": yaml_text},
            headers={"X-API-Key": key},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 1


def test_open_generate_file(client, admin_user, admin_headers):
    key = _make_key(client, admin_headers)
    _ensure_llm_config(client, admin_headers)
    yaml_text = "cases:\n  - module: M\n    feature: F\n    description: D\n    keywords: [k]\n"
    with patch("autocase.llm_client.generate_llm_cases", side_effect=lambda spec, cfg, prompt: _fake_items(spec)), \
         patch("autocase.llm_client.generate_module_code", return_value="MOD"):
        resp = client.post(
            "/api/v1/open/generate-file",
            files={"file": ("cases.yaml", yaml_text, "application/x-yaml")},
            headers={"X-API-Key": key},
        )
    assert resp.status_code == 200, resp.text
    assert resp.json()["total"] == 1


def test_open_generate_no_input_400(client, admin_user, admin_headers):
    key = _make_key(client, admin_headers)
    resp = client.post("/api/v1/open/generate", json={}, headers={"X-API-Key": key})
    assert resp.status_code == 400


def test_open_generate_sync_limit(client, admin_user, admin_headers):
    key = _make_key(client, admin_headers)
    cases = [{"module": f"M{i}", "feature": f"F{i}"} for i in range(25)]
    resp = client.post("/api/v1/open/generate", json={"cases": cases}, headers={"X-API-Key": key})
    assert resp.status_code == 400
    assert "async" in resp.json()["detail"] or "异步" in resp.json()["detail"]


@patch("app.api.v1.open_api.generate_job.delay")
def test_open_generate_async(mock_delay, client, admin_user, admin_headers):
    key = _make_key(client, admin_headers)
    resp = client.post(
        "/api/v1/open/generate-async",
        json={"cases": [{"module": "M", "feature": "F"}]},
        headers={"X-API-Key": key},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"
    assert body["job_id"]
    mock_delay.assert_called_once()

    # poll status
    st = client.get(f"/api/v1/open/jobs/{body['job_id']}", headers={"X-API-Key": key})
    assert st.status_code == 200
    assert st.json()["job_id"] == body["job_id"]
