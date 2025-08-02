import sys
import structlog

from fastapi import APIRouter, status
from src.repositories.doc_analyser_repository import DocAnalyserRepository
from src.utils.custom_exception import CustomException
from fastapi import UploadFile, File
from fastapi import HTTPException

router = APIRouter()

class DocAnalyserController:
    def __init__(self):
        """
        Initializes the DocAnalyserController.
        This controller handles document analysis related endpoints.
        """
        self.log = structlog.get_logger(self.__class__.__name__)
        self.repository = DocAnalyserRepository()

    async def analyse_document(self, data: UploadFile = File(...)):
        """
        Endpoint to upload a document to the document portal to analyze it.
        """
        try:
            self.log.info("Document analysis started")
            
            response = await self.repository.analyse_document(data)
            
            self.log.info("Document analysis completed successfully", response=response)
            
            return response
            
        except ValueError as ve:
            error_msg = CustomException(str(ve), sys).__str__()
            self.log.error("Document analysis failed", error_msg=error_msg)
            raise HTTPException(status_code=400, detail=f"{error_msg}")
        
        except Exception as e:
            error_msg = CustomException(str(e), sys).__str__()
            self.log.error("Document analysis failed", error_msg=error_msg)
            raise HTTPException(status_code=500, detail=f"Unexpected error during document upload.")

# Initialize the controller      
doc_analyser_controller = DocAnalyserController()

# Define the endpoints for the router
# Each endpoint is defined with its path, method, and handler.
endpoints = [
    {
        "path": "/analyze",
        "method": "post",
        "handler": doc_analyser_controller.analyse_document
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
