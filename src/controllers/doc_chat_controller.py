import sys
import structlog

from fastapi import APIRouter, status
from src.utils.custom_exception import CustomException
from fastapi import UploadFile, File
from fastapi import HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from src.repositories.doc_chat_repository import DocChatRepository
from src.models.requests import ChatRequest
from typing import AsyncIterator

router = APIRouter()

class DocChatController:
    def __init__(self):
        """
        Initializes the DocChatController.
        This controller handles document chat related endpoints.
        """
        self.log = structlog.get_logger(self.__class__.__name__)
        self.repository = DocChatRepository()

    async def upload_document(self, client_id: str, product_id: str, data: UploadFile = File(...)):
        """
        Endpoint to upload a document for chat analysis.
        """
        try:
            self.log.info("Document chat started")

            response = await self.repository.upload_document(client_id=client_id, product_id=product_id, data=data)

            self.log.info("Document upload completed successfully", response=response)

            return response
            
        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("Upload document failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{ve}")
        
        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("Upload document failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during document upload.")
        
    async def vectorize_document(self, client_id: str, product_id: str):
        """
        Endpoint to vectorize a document for chat analysis.
        """
        try:
            self.log.info("Document vectorization started")

            await self.repository.vectorize_document(client_id=client_id, product_id=product_id)

            self.log.info("Document vectorization completed successfully")

            return JSONResponse(content="Document vectorization completed successfully")

        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("Vectorize document failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{ve}")

        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("Vectorize document failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during document vectorization.")
        
    async def chat(self, chat_request: ChatRequest):
        try:
            self.log.info("Chat request received", chat_request=chat_request)

            response = await self.repository.chat(chat_request)

            self.log.info("Chat response generated successfully", response=response)

            return JSONResponse(content=response)

        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("Chat request failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{ve}")

        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("Chat request failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during chat processing.")
        
    async def a_chat(self, chat_request: ChatRequest):
        chain = await self.repository.chat_stream()
        result = await chain.ainvoke(
            {
                "question": chat_request["query"]
            }
        )
        return {
            "answer": result
        }
        
    async def chat_stream(self, chat_request: ChatRequest):
        """
        Streams tokens using Server-Sent Events (SSE).
        Each SSE message is a line:  'data: <chunk>\\n\\n'
        The stream terminates with:   'data: [DONE]\\n\\n'
        """

        async def sse_event_gen() -> AsyncIterator[str]:
            # small heartbeat to keep certain proxies happy
            yield ": ping\n\n"

            chain = await self.repository.chat_stream()
            # we'll stream token chunks by listening to LangChain's event stream
            async for token in chain.astream(
                {
                    "question": chat_request["query"],
                },
                version="v1",
            ):
                if token:                             # token is already a STRING
                    yield f"data: {token}\n\n"

            yield "data: [DONE]\n\n"

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # prevents buffering on some proxies
        }
        
        return StreamingResponse(sse_event_gen(), media_type="text/event-stream", headers=headers)

# Initialize the controller
doc_chat_controller = DocChatController()

# Define the endpoints for the router
# Each endpoint is defined with its path, method, and handler.
endpoints = [
    {
        "path": "/upload",
        "method": "post",
        "handler": doc_chat_controller.upload_document
    },
    {
        "path": "/vectorize",
        "method": "post",
        "handler": doc_chat_controller.vectorize_document
    },
    {
        "path": "/chat",
        "method": "post",
        "handler": doc_chat_controller.chat
    },
    {
        "path": "/a_chat",
        "method": "post",
        "handler": doc_chat_controller.a_chat
    },
    {
        "path": "/chat_stream",
        "method": "post",
        "handler": doc_chat_controller.chat_stream
    }
]

# Register the endpoints with the router
for endpoint in endpoints:
    router.add_api_route(
        path=endpoint["path"],
        endpoint=endpoint["handler"],
        methods=[endpoint["method"]],
        status_code=status.HTTP_200_OK
    )
