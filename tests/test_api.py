import requests

BASE_URL = "http://localhost:5000"

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_submit_feedback():
    payload = {
        "customer_id": "test_user",
        "feedback_text": "This product is amazing",
        "timestamp": "2026-03-01T10:00:00Z"
    }

    response = requests.post(f"{BASE_URL}/feedback", json=payload)

    assert response.status_code == 202
    assert "message_id" in response.json()
