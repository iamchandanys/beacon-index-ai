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

def test_upload_document_missing_fields(client: TestClient):
    response = client.post("/upload-document", json={"client_id": "", "product_id": ""})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {"loc": ["body", "client_id"], "msg": "Required field is not provided.", "type": "value_error.missing"},
            {"loc": ["body", "product_id"], "msg": "Required field is not provided.", "type": "value_error.missing"}
        ]
    }