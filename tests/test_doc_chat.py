from fastapi.testclient import TestClient

def test_upload_document_missing_document(client: TestClient):
    # No document file is passed in the request, but valid client_id and product_id
    response = client.post(
        "/doc-chat/upload?client_id=b4d9e62a-8c41-4d3a-a7cc-0164a214c086&product_id=47cd74ea-0422-4390-86b0-58aa94b9b15e",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        data=""
    )
    assert response.status_code == 422
    assert any("Field required" in error["msg"] for error in response.json()["detail"])

def test_upload_document_missing_client_and_product_id(client: TestClient):
    # Document file is passed, but client_id and product_id are missing
    files = {"document": ("test.txt", b"dummy content")}
    response = client.post(
        "/doc-chat/upload",
        headers={
            "Accept": "application/json"
        },
        files=files
    )
    assert response.status_code == 422
    assert any("Field required" in error["msg"] for error in response.json()["detail"])
    
def test_upload_document_no_data(client: TestClient):
    response = client.post(
        "/doc-chat/upload?client_id=someid&product_id=someprod",
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        data=""
    )
    assert response.status_code == 422
      
def test_vectorize_invalid_client_and_product_id(client: TestClient):
    response = client.post(
        "/doc-chat/vectorize?client_id=invalid_client_id&product_id=invalid_product_id",
        headers={"accept": "application/json"},
        data=""
    )
    assert response.status_code == 500
    assert response.json() == {
        "detail": "Unexpected error during document vectorization."
    }
    
def test_chat_invalid_chat_id(client: TestClient):
    payload = {
        "chat_id": "invalid_chat_id",
        "client_id": "d6b607aa-578f-4916-90fa-e2358f366726",
        "product_id": "15f4193d-1ae5-45b2-8cc3-4a82ac311903",
        "query": "Hello"
    }
    response = client.post(
        "/doc-chat/chat",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=payload
    )
    assert response.status_code in (400, 500)
    assert response.json() == {'detail': 'No chat history found for the given chat_id: invalid_chat_id'}
    
def test_chat_missing_client_and_product_id(client: TestClient):
    payload = {
        "chat_id": "b00b11f0-7f77-4578-b470-ae6123899a99",
        # "client_id" is intentionally omitted
        # "product_id" is intentionally omitted
        "query": "Hello"
    }
    response = client.post(
        "/doc-chat/chat",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=payload
    )
    assert response.status_code == 422
    assert any("Field required" in error["msg"] for error in response.json()["detail"])
    
def test_chat_missing_query_field(client: TestClient):
    payload = {
        "chat_id": "b00b11f0-7f77-4578-b470-ae6123899a99",
        "client_id": "d6b607aa-578f-4916-90fa-e2358f366726",
        "product_id": "15f4193d-1ae5-45b2-8cc3-4a82ac311903"
        # "query" is intentionally omitted
    }
    response = client.post(
        "/doc-chat/chat",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json"
        },
        json=payload
    )
    assert response.status_code == 422
    assert any("Field required" in error["msg"] for error in response.json()["detail"])