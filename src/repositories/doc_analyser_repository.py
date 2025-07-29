import uuid

from typing import BinaryIO
from src.services.blob_service import BlobService
from fastapi import UploadFile, File

class DocAnalyserRepository:
    def __init__(self):
        self.blob_service = BlobService()

    async def upload_document(self, data: UploadFile = File(...)) -> str:
        """
        Uploads a document to Azure Blob Storage.
        
        :param data: File-like object containing the document data.
        :return: URL of the uploaded document.
        """
        
        # Validate the file is not empty
        if data.file is None or data.file.closed:
            raise ValueError("File is empty or not provided.")
        
        # Validate the file type
        if data.content_type != "application/pdf":
            raise ValueError("Only PDF files are allowed.")
        
        # Validate the file size (limit to 2 MB)
        if data.size > 2 * 1024 * 1024:  # 2 MB limit
            raise ValueError("File size exceeds the 2 MB limit.")
        
        blob_name = f"{uuid.uuid4()}"
        content_type = "application/pdf"

        return self.blob_service.upload_stream("document-analysis", blob_name, data.file, content_type)
