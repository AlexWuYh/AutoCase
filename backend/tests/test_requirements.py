"""Requirement group + requirement + YAML tests."""
from __future__ import annotations


# ─── Group CRUD ─────────────────────────────────────────────────────────

def test_create_group(client, admin_user, admin_headers):
    resp = client.post(
        "/api/v1/requirement-groups",
        json={"name": "Project A", "description": "test desc"},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Project A"
    assert body["owner_id"] == admin_user.id
    assert body["owner_username"] == "admin"
    assert body["requirement_count"] == 0


def test_list_groups_sees_own(client, admin_user, regular_user, admin_headers, user_headers):
    # admin creates one
    client.post(
        "/api/v1/requirement-groups",
        json={"name": "Admin Group"},
        headers=admin_headers,
    )
    # alice creates one
    client.post(
        "/api/v1/requirement-groups",
        json={"name": "Alice Group"},
        headers=user_headers,
    )
    # admin lists (default sees all for admin)
    admin_list = client.get("/api/v1/requirement-groups", headers=admin_headers).json()
    assert admin_list["total"] == 2
    # admin lists with scope=mine
    admin_mine = client.get("/api/v1/requirement-groups?scope=mine", headers=admin_headers).json()
    assert admin_mine["total"] == 1
    assert admin_mine["items"][0]["name"] == "Admin Group"
    # alice lists - only sees her own
    alice_list = client.get("/api/v1/requirement-groups", headers=user_headers).json()
    assert alice_list["total"] == 1
    assert alice_list["items"][0]["name"] == "Alice Group"


def test_non_admin_cannot_use_scope_all(client, regular_user, user_headers):
    resp = client.get(
        "/api/v1/requirement-groups?scope=all", headers=user_headers
    )
    assert resp.status_code == 403


def test_admin_can_use_scope_all(client, admin_user, regular_user, admin_headers, user_headers):
    client.post(
        "/api/v1/requirement-groups",
        json={"name": "X"},
        headers=user_headers,
    )
    resp = client.get(
        "/api/v1/requirement-groups?scope=all", headers=admin_headers
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 1


def test_get_group_forbidden_for_non_owner(client, admin_user, regular_user, admin_headers, user_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "Admin Only"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    # alice tries to fetch
    resp = client.get(f"/api/v1/requirement-groups/{gid}", headers=user_headers)
    assert resp.status_code == 403


def test_update_group_owner(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "Old"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    resp = client.put(
        f"/api/v1/requirement-groups/{gid}",
        json={"name": "New", "description": "updated"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New"


def test_delete_group_cascades_requirements(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "To Delete"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"items": [
            {"module": "M", "feature": "F", "description": "D", "keywords": []}
        ]},
        headers=admin_headers,
    )
    resp = client.delete(f"/api/v1/requirement-groups/{gid}", headers=admin_headers)
    assert resp.status_code == 200


# ─── Requirements ───────────────────────────────────────────────────────

def test_batch_create_requirements_append(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    resp = client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"items": [
            {"module": "M1", "feature": "F1", "description": "D1", "keywords": ["a"]},
            {"module": "M2", "feature": "F2", "description": "D2", "keywords": ["b", "c"]},
        ]},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert len(body) == 2
    assert body[0]["sort_order"] == 0
    assert body[1]["sort_order"] == 1
    assert body[1]["keywords"] == ["b", "c"]


def test_batch_create_replace_clears_existing(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    # add 3 first
    client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"items": [
            {"module": "A", "feature": "a", "description": "", "keywords": []},
            {"module": "B", "feature": "b", "description": "", "keywords": []},
            {"module": "C", "feature": "c", "description": "", "keywords": []},
        ]},
        headers=admin_headers,
    )
    # replace with 1
    resp = client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"mode": "replace", "items": [
            {"module": "Z", "feature": "z", "description": "new", "keywords": []}
        ]},
        headers=admin_headers,
    )
    assert resp.status_code == 201
    listing = client.get(
        f"/api/v1/requirement-groups/{gid}/requirements", headers=admin_headers
    ).json()
    assert listing["total"] == 1
    assert listing["items"][0]["module"] == "Z"


def test_update_requirement(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    cr = client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"items": [
            {"module": "M", "feature": "F", "description": "old", "keywords": []}
        ]},
        headers=admin_headers,
    )
    rid = cr.json()[0]["id"]
    resp = client.put(
        f"/api/v1/requirement-groups/requirements/{rid}",
        json={"description": "new"},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "new"


def test_delete_requirement(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    cr = client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"items": [
            {"module": "M", "feature": "F", "description": "", "keywords": []}
        ]},
        headers=admin_headers,
    )
    rid = cr.json()[0]["id"]
    resp = client.delete(
        f"/api/v1/requirement-groups/requirements/{rid}",
        headers=admin_headers,
    )
    assert resp.status_code == 200


def test_requirement_search(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    client.post(
        f"/api/v1/requirement-groups/{gid}/requirements",
        json={"items": [
            {"module": "Org", "feature": "Create", "description": "make a new venue", "keywords": []},
            {"module": "Order", "feature": "Refund", "description": "refund a request", "keywords": []},
        ]},
        headers=admin_headers,
    )
    resp = client.get(
        f"/api/v1/requirement-groups/{gid}/requirements?search=refund",
        headers=admin_headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert items[0]["feature"] == "Refund"


# ─── YAML import / export ──────────────────────────────────────────────

SAMPLE_YAML = """\
cases:
  - module: 系统设置 / 机构场地
    feature: 机构场地管理-新增场地
    description: 支持管理员新增场地，包含名称、地址、容量
    keywords:
      - 场地
      - 校验
  - module: 订单中心
    feature: 退款申请-发起
    description: 用户发起退款申请
    keywords: 退款, 订单
"""


def test_import_yaml_from_text(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    resp = client.post(
        f"/api/v1/requirement-groups/{gid}/import-yaml?mode=append",
        data={"text": SAMPLE_YAML},
        headers=admin_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["imported"] == 2
    assert body["total_in_file"] == 2
    listing = client.get(
        f"/api/v1/requirement-groups/{gid}/requirements", headers=admin_headers
    ).json()
    assert listing["total"] == 2
    assert listing["items"][1]["keywords"] == ["退款", "订单"]


def test_import_yaml_from_file(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    files = {"file": ("cases.yaml", SAMPLE_YAML, "application/x-yaml")}
    resp = client.post(
        f"/api/v1/requirement-groups/{gid}/import-yaml?mode=append",
        files=files,
        headers=admin_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["imported"] == 2


def test_import_yaml_invalid_400(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    resp = client.post(
        f"/api/v1/requirement-groups/{gid}/import-yaml",
        data={"text": "this is: not: valid: yaml: at all", "mode": "append"},
        headers=admin_headers,
    )
    # Bad YAML that doesn't parse to valid CaseSpecs → 400
    assert resp.status_code == 400


def test_export_yaml_roundtrip(client, admin_user, admin_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "G"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    client.post(
        f"/api/v1/requirement-groups/{gid}/import-yaml?mode=replace",
        data={"text": SAMPLE_YAML},
        headers=admin_headers,
    )
    resp = client.get(
        f"/api/v1/requirement-groups/{gid}/export-yaml", headers=admin_headers
    )
    assert resp.status_code == 200
    yaml_text = resp.text
    assert "cases:" in yaml_text
    assert "系统设置 / 机构场地" in yaml_text
    assert "退款" in yaml_text


def test_export_yaml_forbidden_for_non_owner(client, admin_user, regular_user, admin_headers, user_headers):
    r = client.post(
        "/api/v1/requirement-groups",
        json={"name": "Admin"},
        headers=admin_headers,
    )
    gid = r.json()["id"]
    resp = client.get(
        f"/api/v1/requirement-groups/{gid}/export-yaml", headers=user_headers
    )
    assert resp.status_code == 403
