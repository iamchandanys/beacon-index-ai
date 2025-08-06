import uuid
import aiohttp
import structlog
import fitz # From PyMuPDF for PDF processing

from src.services.azure_blob_storage.blob_service import BlobService
from fastapi import UploadFile, File
from langchain.document_loaders import PyPDFLoader
from src.utils.chunk_pdf import ChunkPDF
from src.services.large_language_models.llm_service import LLMService

class DocChatRepository:
    def __init__(self):
        self.blob_service = BlobService()
        self.log = structlog.get_logger(self.__class__.__name__)
        self.azOpenAIllm = LLMService.getAzOpenAIllm()
    
    async def upload_document(self, client_id: str, product_id: str, data: UploadFile = File(...)) -> str:
        """
        Uploads a document to Azure Blob Storage.
        
        :param data: File-like object containing the document data.
        :param client_id: Client ID for the document.
        :param product_id: Product ID for the document.
        :return: URL of the uploaded document.
        """
        self.log.info("Validating uploaded file", filename=data.filename)
        
        # Validate the file is not empty
        if data.file is None or data.file.closed:
            self.log.error("File is empty or not provided")
            raise ValueError("File is empty or not provided.")
        
        # Validate the file type
        if data.content_type != "application/pdf":
            self.log.error("Invalid file type", content_type=data.content_type)
            raise ValueError("Only PDF files are allowed.")
        
        # Validate the file size (limit to 2 MB)
        if data.size > 2 * 1024 * 1024:  # 2 MB limit
            self.log.error("File size exceeds limit", size=data.size)
            raise ValueError("File size exceeds the 2 MB limit.")
        
        blob_name = f"{uuid.uuid4()}.pdf"
        content_type = "application/pdf"

        blob_path = f"{client_id}/{product_id}/{blob_name}"
        
        self.log.info("Uploading file to Azure Blob Storage", container="document-chat", blob_path=blob_path)

        file_url = self.blob_service.upload_stream("document-chat", blob_path, data.file, content_type)
        
        self.log.info("File uploaded successfully", file_url=file_url)
        
        return file_url
    
    async def vectorize_document(self, client_id: str, product_id: str) -> None:
        file_urls = await self.blob_service.list_files_in_folder("document-chat", f"{client_id}/{product_id}/")
        
        text_chunks = []
        
        for file_url in file_urls:
            pdf_chunks = await ChunkPDF(self.azOpenAIllm).chunk_pdf(file_url)
            text_chunks.extend(pdf_chunks)