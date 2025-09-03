from typing_extensions import TypedDict

class ChatRequest(TypedDict):
    chat_id: str
    client_id: str
    product_id: str
    user_id: str | None
    query: str
