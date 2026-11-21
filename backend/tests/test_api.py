"""
API Integration Tests for AI Controller Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "AI Expense Tracker Controller"


def test_chat_unauthorized_missing_header(client):
    response = client.post("/chat", json={"message": "What did I spend?"})
    assert response.status_code == 401
    assert "Authorization header" in response.json()["detail"]


def test_chat_unauthorized_invalid_token(client):
    response = client.post(
        "/chat",
        headers={"Authorization": "Bearer invalid_garbage_token"},
        json={"message": "What did I spend?"}
    )
    assert response.status_code == 401


def test_chat_authorized_success(client, seeded_firebase_mock, mock_user_a):
    headers = {"Authorization": f"Bearer test-token-{mock_user_a['uid']}"}
    response = client.post(
        "/chat",
        headers=headers,
        json={"message": "Maine is month kitne paise kharch kiye?", "month": 9, "year": 2026}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["intent"] == "expense_query"
    assert "28,200" in data["answer"]
    assert "suggested_followups" in data
    assert len(data["suggested_followups"]) > 0


def test_user_financial_summary_endpoint(client, seeded_firebase_mock, mock_user_a):
    headers = {"Authorization": f"Bearer test-token-{mock_user_a['uid']}"}
    response = client.get(
        "/user/financial-summary?month=9&year=2026",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == mock_user_a["uid"]
    assert data["total_spent"] == 28200
    assert data["total_income"] == 75000
    assert data["net_savings"] == 46800
    assert data["budget"] == 45000
    assert data["remaining_budget"] == 16800


def test_chat_invalid_payload_rejected(client, mock_user_a):
    headers = {"Authorization": f"Bearer test-token-{mock_user_a['uid']}"}
    # Empty message should fail Pydantic validation (min_length=1)
    response = client.post(
        "/chat",
        headers=headers,
        json={"message": ""}
    )
    assert response.status_code == 422
