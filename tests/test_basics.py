import os

from fastapi.testclient import TestClient

# To disable opening the DeepEval dashboard whenever a request is made
os.environ["DEEPEVAL_DASHBOARD_DISABLED"] = "1"

# Naming Convention: Functions starting with test_ are automatically discovered and run by test frameworks like pytest or unittest.

def test_read_main(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Beacon API"}

def test_refresh_config(client: TestClient):
    response = client.post("/refresh-config")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
def test_nonexistent_endpoint(client: TestClient):
    response = client.get("/does-not-exist")
    assert response.status_code == 404