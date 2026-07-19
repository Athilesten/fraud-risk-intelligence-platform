from fastapi.testclient import TestClient

from api.main import app


def test_health_endpoint_is_public():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_demo_login_returns_bearer_token():
    client = TestClient(app)
    response = client.post(
        "/auth/login",
        json={"email": "admin@fraud.local", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
