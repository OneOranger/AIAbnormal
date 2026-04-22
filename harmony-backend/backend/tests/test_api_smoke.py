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


def test_reconciliation_match():
    r = client.post("/reconciliation/match")
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["total"] >= data["matched"]


def test_ingest_minimal_payment_event():
    r = client.post("/ingest", json={
        "orderNo": "PAY-TEST-INGEST-001",
        "eventTime": "2026-04-22T02:14:00Z",
        "userId": "U-INGEST-001",
        "merchantId": "M-INGEST-001",
        "amount": 68000,
        "currency": "CNY",
        "channel": "visa",
        "ip": "45.12.88.10",
        "ipCountry": "RU",
        "device": "Headless Chrome",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["orderNo"] == "PAY-TEST-INGEST-001"
