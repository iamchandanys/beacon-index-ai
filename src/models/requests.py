from typing import TypedDict

class ChatRequest(TypedDict):
    chat_id: str
    client_id: str
    product_id: str
    query: str
