from fastapi.testclient import TestClient

# Naming Convention: Functions starting with test_ are automatically discovered and run by test frameworks like pytest or unittest.
def test_read_main(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Document Portal API"}

def test_refresh_config(client: TestClient):
    response = client.post("/refresh-config")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}