"""Generation job tests (mock Celery + LLM)."""
from __future__ import annotations

from unittest.mock import patch


def _fake_case(idx):
    return {"type": "功能测试", "name": f"用例{idx}", "priority": "2", "pre": "无",
            "steps": [f"步骤{idx}"], "expected": ["期望"], "stage": "功能测试阶段"}


@patch("app.api.v1.jobs.generate_job.delay")
def test_create_job_succeeds(mock_delay, client, admin_user, admin_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    gid = g.json()["id"]
    client.post(f"/api/v1/requirement-groups/{gid}/requirements",
                json={"items": [{"module": "M", "feature": "F", "description": "D", "keywords": []}]},
                headers=admin_headers)
    resp = client.post("/api/v1/jobs", json={"group_id": gid}, headers=admin_headers)
    assert resp.status_code == 202
    assert resp.json()["total"] == 1
    mock_delay.assert_called_once()


@patch("app.api.v1.jobs.generate_job.delay")
def test_create_job_no_requirements(mock_delay, client, admin_user, admin_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    resp = client.post("/api/v1/jobs", json={"group_id": g.json()["id"]}, headers=admin_headers)
    assert resp.status_code == 400
    mock_delay.assert_not_called()


@patch("app.api.v1.jobs.generate_job.delay")
def test_list_jobs(mock_delay, client, admin_user, admin_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    gid = g.json()["id"]
    client.post(f"/api/v1/requirement-groups/{gid}/requirements",
                json={"items": [{"module": "M", "feature": "F", "description": "D", "keywords": []}]},
                headers=admin_headers)
    client.post("/api/v1/jobs", json={"group_id": gid}, headers=admin_headers)
    resp = client.get("/api/v1/jobs", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@patch("app.api.v1.jobs.generate_job.delay")
def test_job_requires_access(mock_delay, client, admin_user, regular_user, admin_headers, user_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    gid = g.json()["id"]
    client.post(f"/api/v1/requirement-groups/{gid}/requirements",
                json={"items": [{"module": "M", "feature": "F", "description": "D", "keywords": []}]},
                headers=admin_headers)
    jr = client.post("/api/v1/jobs", json={"group_id": gid}, headers=admin_headers)
    jid = jr.json()["id"]
    assert client.get(f"/api/v1/jobs/{jid}", headers=user_headers).status_code == 403


@patch("app.api.v1.jobs.generate_job.delay")
def test_cancel_job(mock_delay, client, admin_user, admin_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    gid = g.json()["id"]
    client.post(f"/api/v1/requirement-groups/{gid}/requirements",
                json={"items": [{"module": "M", "feature": "F", "description": "D", "keywords": []}]},
                headers=admin_headers)
    jr = client.post("/api/v1/jobs", json={"group_id": gid}, headers=admin_headers)
    jid = jr.json()["id"]
    resp = client.delete(f"/api/v1/jobs/{jid}", headers=admin_headers)
    assert resp.status_code == 200


@patch("app.api.v1.jobs.generate_job.delay")
def test_export_xlsx(mock_delay, client, admin_user, admin_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    gid = g.json()["id"]
    client.post(f"/api/v1/requirement-groups/{gid}/requirements",
                json={"items": [{"module": "M", "feature": "F", "description": "D", "keywords": []}]},
                headers=admin_headers)
    jr = client.post("/api/v1/jobs", json={"group_id": gid}, headers=admin_headers)
    jid = jr.json()["id"]
    resp = client.get(f"/api/v1/jobs/{jid}/export?format=xlsx", headers=admin_headers)
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers.get("content-type", "")


@patch("app.api.v1.jobs.generate_job.delay")
def test_export_csv(mock_delay, client, admin_user, admin_headers):
    g = client.post("/api/v1/requirement-groups", json={"name": "G"}, headers=admin_headers)
    gid = g.json()["id"]
    client.post(f"/api/v1/requirement-groups/{gid}/requirements",
                json={"items": [{"module": "M", "feature": "F", "description": "D", "keywords": []}]},
                headers=admin_headers)
    jr = client.post("/api/v1/jobs", json={"group_id": gid}, headers=admin_headers)
    jid = jr.json()["id"]
    resp = client.get(f"/api/v1/jobs/{jid}/export?format=csv", headers=admin_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")
