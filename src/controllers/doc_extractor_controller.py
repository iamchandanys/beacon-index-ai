import sys
import structlog

from src.repositories.doc_extractor_repository import DocExtractorRepository
from src.utils.custom_exception import CustomException
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from fastapi import HTTPException

router = APIRouter()

class DocExtractorController:
    def __init__(self):
        self.log = structlog.get_logger(self.__class__.__name__)
        self.repository = DocExtractorRepository()
        
    async def sync_documents(self, client_id: str, product_id: str):
        """
        Endpoint to synchronize documents for chat analysis.
        """
        try:
            self.log.info("Document synchronization started")

            await self.repository.sync_documents(client_id=client_id, product_id=product_id)

            self.log.info("Document synchronization completed successfully")

            return JSONResponse(content="Document synchronization completed successfully")

        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("Sync documents failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{ve}")

        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("Sync documents failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during document synchronization.")

doc_extractor_controller = DocExtractorController()

endpoints = [
    {
        "path": "/sync",
        "method": "post",
        "handler": doc_extractor_controller.sync_documents
    }
]

for endpoint in endpoints:
    router.add_api_route(
        path=endpoint["path"],
        endpoint=endpoint["handler"],
        methods=[endpoint["method"]],
        status_code=status.HTTP_200_OK
    )
