import aiohttp
import uuid
import structlog
import fitz # From PyMuPDF for PDF processing

from fastapi import UploadFile, File
from datetime import datetime
from langchain.output_parsers import OutputFixingParser
from langchain_core.output_parsers import JsonOutputParser
from src.services.azure.blob import BlobService
from src.services.llm.providers import LLMService
from src.services.prompts.prompting import *
from src.models.doc_analyser_model import DocAnalyserMetadata

class DocAnalyserRepository:
    def __init__(self):
        self.azOpenA_llm = LLMService().getAzOpenAIllm()
        self.blob_service = BlobService()
        self.log = structlog.get_logger(self.__class__.__name__)
        
    async def analyse_document(self, data: UploadFile = File(...)) -> dict:
        """
        Analyzes a document by uploading it to Azure Blob Storage, reading its content,
        and extracting structured metadata using a language model.
        
        :param data: File-like object containing the document data.
        :return: Dictionary containing the extracted metadata.
        """
        self.log.info("Starting document analysis", filename=data.filename)
        
        file_url = await self._upload_document(data)
        
        self.log.info("Document uploaded to Azure Blob Storage", file_url=file_url)
        
        file_text = await self._read_file(file_url)
        
        self.log.info("Extracted text from document", text_length=len(file_text))
        
        response = await self._analyze_document(file_text)
        
        self.log.info("Document analysis completed")
        
        return response

    async def _upload_document(self, data: UploadFile = File(...)) -> str:
        """
        Uploads a document to Azure Blob Storage.
        
        :param data: File-like object containing the document data.
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
        
        client_id = "a5f4ca5e-36f6-4eb3-93fe-517b16f66f4d" #Todo: Replace with actual client ID
        product_id = "a88cffc2-3f4d-4351-81b8-39ea3317a731" #Todo: Replace with actual product ID
        version = datetime.now().strftime("%d%m%Y%H%M%S")
        blob_name = f"{uuid.uuid4()}.pdf"
        content_type = "application/pdf"

        blob_path = f"{client_id}/{product_id}/{version}/{blob_name}"
        
        self.log.info("Uploading file to Azure Blob Storage", container="document-analysis", blob_path=blob_path)
        
        file_url = self.blob_service.upload_stream("document-analysis", blob_path, data.file, content_type)
        
        self.log.info("File uploaded successfully", file_url=file_url)
        
        return file_url

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
        self.log.info("Starting to read PDF file from URL")

        text_chunks = []

        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as response:
                response.raise_for_status()
                pdf_bytes = await response.read()

        self.log.info("PDF file downloaded successfully", file_size=len(pdf_bytes))

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page_num, page in enumerate(doc, start=1):
                page_text = page.get_text()
                text_chunks.append(f"\n--- Page {page_num} ---\n{page_text}")

        text = "\n".join(text_chunks)

        self.log.info("Completed text extraction from PDF", total_text_length=len(text))

        return text

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
        self.log.info("Initializing output parsers for document analysis")
        
        # Use JsonOutputParser to get well-structured JSON responses from a language model
        parser = JsonOutputParser(pydantic_object=DocAnalyserMetadata)
        # Use OutputFixingParser to automatically fix and get responses that have small formatting errors, making your data extraction more reliable and error-proof
        fixing_parser = OutputFixingParser.from_llm(llm=self.azOpenA_llm, parser=parser)

        self.log.info("Creating prompt chain for document analysis")
        
        # Create a prompt chain that combines the chat prompt template with the language model and output parser
        # The prompt chain will analyze the document text and return structured metadata in JSON format
        chain = doc_analyse_prompt | self.azOpenA_llm | fixing_parser
        
        self.log.info("Invoking prompt chain for document analysis")
        
        response = await chain.ainvoke({
            "format_instructions": parser.get_format_instructions(),
            "document_text": doc_text
        })
        
        self.log.info("Received response from language model")
        
        return response
