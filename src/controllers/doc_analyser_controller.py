import sys

from fastapi import APIRouter, status
from src.repositories.doc_analyser_repository import DocAnalyserRepository
from fastapi import UploadFile, File
from fastapi import HTTPException
from logger.custom_struct_logger import CustomStructLogger

router = APIRouter()

class DocAnalyserController:
    def __init__(self):
        """
        Initializes the DocAnalyserController.
        This controller handles document analysis related endpoints.
        """
        self.repository = DocAnalyserRepository()
        customStructLogger = CustomStructLogger()
        self.logger = customStructLogger.get_logger(__file__)

    async def upload_document(self, data: UploadFile = File(...)):
        """
        Endpoint to upload a document to the document portal to analyze it.
        """
        try:
            
            self.logger.info(f"Uploading document to the document portal. File name: {data.filename}, Content type: {data.content_type}")
            
            response = await self.repository.upload_document(data)
            
            self.logger.info("Document uploaded successfully")

            return {
                "message": "Document uploaded successfully.",
                "url": response
            }
            
        except ValueError as ve:
            
            raise HTTPException(status_code=400, detail=f"{str(ve)}")
        
        except Exception as e:

            raise HTTPException(status_code=500, detail=f"Unexpected error during document upload: {str(e)}")
    
    async def analyze_document(self):
        """
        Endpoint to analyze a document.
        This is a placeholder for the actual implementation.
        """
        
        return {
            "message": "Document analysis is not yet implemented."
        }

# Initialize the controller      
doc_analyser_controller = DocAnalyserController()

# Define the endpoints for the router
# Each endpoint is defined with its path, method, and handler.
endpoints = [
    {
        "path": "/upload",
        "method": "post",
        "handler": doc_analyser_controller.upload_document
    },
    {
        "path": "/analyze",
        "method": "post",
        "handler": doc_analyser_controller.analyze_document
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
