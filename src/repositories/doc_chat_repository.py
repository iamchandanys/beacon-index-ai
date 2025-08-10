import uuid
import structlog

from fastapi import UploadFile, File
from langchain.schema import Document
from datetime import datetime, timezone
from src.services.azure_blob_storage.blob_service import BlobService
from src.services.large_language_models.llm_service import LLMService
from src.services.vector_database.faiss import FaissService
from src.services.cosmos_service.cosmos_service import CosmosService
from src.models.doc_chat_model import DocChatModel
from src.utils.chunk_pdf import ChunkPDF

class DocChatRepository:
    def __init__(self):
        self.log = structlog.get_logger(self.__class__.__name__)
        self.blob_service = BlobService()
        self.cosmos_service = CosmosService()
        self.llm_service = LLMService()
        self.faiss_service = FaissService()
        self.azOpenAIllm = self.llm_service.getAzOpenAIllm()
    
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
        file_urls = self.blob_service.list_files_in_folder("document-chat", f"{client_id}/{product_id}/")
        
        text_chunks: list[Document] = []
        
        for file_url in file_urls:
            chunk_pdf = ChunkPDF(self.azOpenAIllm)
            pdf_chunks = chunk_pdf.chunk_pdf(file_url)
            text_chunks.extend(pdf_chunks)
            
        if len(text_chunks) <= 0:
            self.log.error("No text chunks found for document vectorization")
            raise ValueError("No text chunks found for document vectorization")

        faiss_service = FaissService()

        vector_store = faiss_service.create_vector_store(client_id, product_id, text_chunks)

        relevant_docs = vector_store.similarity_search("document drafted by whom?", k=5)
        
        print("Relevant documents:", relevant_docs)

    def init_chat(self, client_id: str, product_id: str):
        now_str = datetime.now(timezone.utc).isoformat()
        
        doc_chat_model = DocChatModel()
        doc_chat_model["id"] = str(uuid.uuid4())
        doc_chat_model["client_id"] = client_id
        doc_chat_model["product_id"] = product_id
        doc_chat_model["messages"] = []
        doc_chat_model["createdAt"] = now_str
        doc_chat_model["updatedAt"] = now_str
        
        self.cosmos_service.init_chat(doc_chat_model)

    async def chat(self, client_id: str, product_id: str, query: str) -> str:
        vector_store = self.faiss_service.load_vector_store(client_id, product_id)

        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        