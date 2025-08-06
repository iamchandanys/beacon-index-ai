import sys
import structlog

from fastapi import APIRouter, status
from src.utils.custom_exception import CustomException
from fastapi import UploadFile, File
from fastapi import HTTPException
from src.repositories.doc_chat_repository import DocChatRepository

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
            raise HTTPException(status_code=400, detail=f"{error_msg}")
        
        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("Upload document failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during document upload.")

# Initialize the controller
doc_chat_controller = DocChatController()

# Define the endpoints for the router
# Each endpoint is defined with its path, method, and handler.
endpoints = [
    {
        "path": "/upload",
        "method": "post",
        "handler": doc_chat_controller.upload_document
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
