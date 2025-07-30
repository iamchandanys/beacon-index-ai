import aiohttp
import uuid
import fitz # From PyMuPDF for PDF processing

from src.services.azure_blob_storage.blob_service import BlobService
from src.services.large_language_models.llm_service import LLMService
from src.services.prompts.prompt_service import *
from src.models.doc_analyser_model import DocAnalyserMetadata
from fastapi import UploadFile, File
from datetime import datetime
from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import JsonOutputParser

class DocAnalyserRepository:
    def __init__(self):
        self.azOpenA_llm = LLMService().getAzOpenAIllm()
        self.blob_service = BlobService()
        
    async def analyse_document(self, data: UploadFile = File(...)) -> dict:
        """
        Analyzes a document by uploading it to Azure Blob Storage, reading its content,
        and extracting structured metadata using a language model.
        
        :param data: File-like object containing the document data.
        :return: Dictionary containing the extracted metadata.
        """
        try:
            
            file_url = await self._upload_document(data)
            file_text = await self._read_file(file_url)
            response = await self._analyze_document(file_text)
            return response
        
        except Exception as e:
            
            raise RuntimeError(f"Failed to analyze document: {e}")

    async def _upload_document(self, data: UploadFile = File(...)) -> str:
        """
        Uploads a document to Azure Blob Storage.
        
        :param data: File-like object containing the document data.
        :return: URL of the uploaded document.
        """
        try:
            
            # Validate the file is not empty
            if data.file is None or data.file.closed:
                raise ValueError("File is empty or not provided.")
            
            # Validate the file type
            if data.content_type != "application/pdf":
                raise ValueError("Only PDF files are allowed.")
            
            # Validate the file size (limit to 2 MB)
            if data.size > 2 * 1024 * 1024:  # 2 MB limit
                raise ValueError("File size exceeds the 2 MB limit.")
            
            client_id = "a5f4ca5e-36f6-4eb3-93fe-517b16f66f4d" #Todo: Replace with actual client ID
            product_id = "a88cffc2-3f4d-4351-81b8-39ea3317a731" #Todo: Replace with actual product ID
            version = datetime.now().strftime("%d%m%Y%H%M%S")
            blob_name = f"{uuid.uuid4()}.pdf"
            content_type = "application/pdf"

            return self.blob_service.upload_stream("document-analysis", f"{client_id}/{product_id}/{version}/{blob_name}", data.file, content_type)
 
        except Exception as e:
            
            raise RuntimeError(f"Failed to upload document: {str(e)}")
    
    async def _read_file(self, file_url: str) -> str:
        """
        Asynchronously reads a PDF file from the given URL and extracts its text content.
        Args:
            file_url (str): The URL of the PDF file to read.
        Returns:
            str: The extracted text from the PDF, with each page separated and labeled.
        Raises:
            RuntimeError: If the file cannot be read or processed.
        """
        try:
            
            text_chunks = []
        
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    response.raise_for_status()
                    pdf_bytes = await response.read()

            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page_num, page in enumerate(doc, start=1):
                    text_chunks.append(f"\n--- Page {page_num} ---\n{page.get_text()}")

            text = "\n".join(text_chunks)
            
            return text
        
        except Exception as e:
            
            raise RuntimeError(f"Failed to read file: {e}")
        
    async def _analyze_document(self, doc_text: str) -> dict:
        """
        Asynchronously analyzes the given document text using a language model and returns structured metadata.
        This method utilizes a JsonOutputParser to extract well-structured JSON responses from the language model,
        and an OutputFixingParser to automatically correct minor formatting errors in the output. The analysis is
        performed by invoking a prompt chain with the provided document text.
        Args:
            doc_text (str): The text content of the document to be analyzed.
        Returns:
            dict: A dictionary containing the extracted metadata from the document.
        """
        try:
            
            # Use JsonOutputParser to get well-structured JSON responses from a language model
            parser = JsonOutputParser(pydantic_object=DocAnalyserMetadata)
            # Use OutputFixingParser to automatically fix and get responses that have small formatting errors, making your data extraction more reliable and error-proof
            fixing_parser = OutputFixingParser.from_llm(llm=self.azOpenA_llm, parser=parser)

            # Create a prompt chain that combines the chat prompt template with the language model and output parser
            # The prompt chain will analyze the document text and return structured metadata in JSON format
            chain = doc_analyse_prompt | self.azOpenA_llm | fixing_parser
            
            response = await chain.ainvoke({
                "format_instructions": parser.get_format_instructions(),
                "document_text": doc_text
            })
            
            return response
        
        except Exception as e:
            
            raise RuntimeError(f"Failed to analyze document: {e}")
