"""基础 API 烟雾测试。"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_list_orders():
    r = client.get("/orders?page=1&pageSize=10")
    assert r.status_code == 200
    data = r.json()
    assert "items" in data and "total" in data
    assert len(data["items"]) <= 10


def test_list_rules():
    r = client.get("/rules")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_list_models():
    r = client.get("/models")
    assert r.status_code == 200


def test_list_policies():
    r = client.get("/policies")
    assert r.status_code == 200
