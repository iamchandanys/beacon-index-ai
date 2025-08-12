import uuid
import structlog

from fastapi import UploadFile, File
from langchain.schema import Document
from datetime import datetime, timezone
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from src.services.azure.blob import BlobService
from src.services.llm.providers import LLMService
from src.services.vectorstores.faiss_store import FaissService
from src.services.azure.cosmos import CosmosService
from src.models.doc_chat_model import DocChatModel
from src.models.requests import ChatRequest
from src.services.extractors.pdf_chunker import ChunkPDF
from src.services.prompts.prompting import contextualize_question_prompt, context_qa_prompt

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

        # Throw error if client_id or product_id is not provided
        if not client_id or not product_id:
            self.log.error("Client ID or Product ID is not provided")
            raise ValueError("Client ID and Product ID must be provided.")

        # Validate the file is not empty
        if data.file is None or data.file.closed:
            self.log.error("File is empty or not provided")
            raise ValueError("File is empty or not provided.")
        
        # Validate the file type
        if data.content_type != "application/pdf":
            self.log.error("Invalid file type", content_type=data.content_type)
            raise ValueError("Only PDF files are allowed.")
        
        # Validate the file size (limit to 5 MB)
        if data.size > 5 * 1024 * 1024:  # 5 MB limit
            self.log.error("File size exceeds limit", size=data.size)
            raise ValueError("File size exceeds the 5 MB limit.")
        
        blob_name = f"{uuid.uuid4()}.pdf"
        content_type = "application/pdf"

        blob_path = f"{client_id}/{product_id}/{blob_name}"
        
        self.log.info("Uploading file to Azure Blob Storage", container="document-chat", blob_path=blob_path)

        file_url = self.blob_service.upload_stream("document-chat", blob_path, data.file, content_type)
        
        self.log.info("File uploaded successfully", file_url=file_url)
        
        return file_url
    
    async def vectorize_document(self, client_id: str, product_id: str) -> None:
        # Throw error if client_id or product_id is not provided
        if not client_id or not product_id:
            self.log.error("Client ID or Product ID is not provided")
            raise ValueError("Client ID and Product ID must be provided.")
        
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

        faiss_service.create_vector_store(client_id, product_id, text_chunks)

    def init_chat(self, client_id: str, product_id: str) -> DocChatModel:
        self.log.info("Initializing new chat", client_id=client_id, product_id=product_id)

        now_str = datetime.now(timezone.utc).isoformat()
        
        doc_chat_model = DocChatModel()
        doc_chat_model["id"] = str(uuid.uuid4())
        doc_chat_model["client_id"] = client_id
        doc_chat_model["product_id"] = product_id
        doc_chat_model["messages"] = []
        doc_chat_model["createdAt"] = now_str
        doc_chat_model["updatedAt"] = now_str
        
        chat_details = self.cosmos_service.init_chat(doc_chat_model)

        self.log.info("Chat initialized successfully", chat_id=doc_chat_model["id"])

        return chat_details

    @staticmethod
    def _format_docs(docs: list[Document]) -> str:
        return "\n\n".join([doc.page_content for doc in docs])

    def _get_chat_history(self, chat_id: str) -> list[AIMessage | HumanMessage | SystemMessage]:
        self.log.info("Fetching chat details", chat_id=chat_id)
        
        chat_history: list[AIMessage | HumanMessage | SystemMessage] = []

        chat_details = self.cosmos_service.get_chat(chat_id)

        for message in chat_details["messages"]:
            for content in message["content"]:
                if message["role"] == "system":
                    chat_history.append(SystemMessage(content["text"]))
                elif message["role"] == "user":
                    chat_history.append(HumanMessage(content["text"]))
                elif message["role"] == "assistant":
                    chat_history.append(AIMessage(content["text"]))

        self.log.info("Chat history fetched successfully", chat_id=chat_id, history_length=len(chat_history))
        
        return chat_history
    
    def _update_chat_history(self, chat_id: str, user_message: str, assistant_message: str) -> None:
        self.log.info("Updating chat history", chat_id=chat_id)

        chat_details = self.cosmos_service.get_chat(chat_id)

        # Append user message
        chat_details["messages"].append({
            "role": "user",
            "content": [{"text": user_message, "type": "text", "tokensUsed": 0}]
        })

        # Append assistant message
        chat_details["messages"].append({
            "role": "assistant",
            "content": [{"text": assistant_message, "type": "text", "tokensUsed": 0}]
        })

        self.cosmos_service.update_chat(chat_details)
        
        self.log.info("Chat history updated successfully", chat_id=chat_id, messages_count=len(chat_details["messages"]))
    
    def chat(self, chat_request: ChatRequest) -> str:
        self.log.info("Loading vector store", client_id=chat_request["client_id"], product_id=chat_request["product_id"])

        # Load the vector store
        vector_store = self.faiss_service.load_vector_store(chat_request["client_id"], chat_request["product_id"])

        # Create retriever from vector store
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})

        self.log.info("Preparing question rewriter and retrieval chain")

        # Rewrite user question with chat history context
        question_rewriter = (
            {
                "input": RunnableLambda(lambda x: x["question"]), 
                "chat_history": RunnableLambda(lambda x: x["chat_history"])
            }
            | contextualize_question_prompt | self.azOpenAIllm | StrOutputParser()
        )

        # Retrieve docs for rewritten question
        retrieve_docs = question_rewriter | retriever | self._format_docs

        # Answer using retrieved docs + original input + chat history
        chain = (
            {
                "context": retrieve_docs,
                "input": RunnableLambda(lambda x: x["question"]),
                "chat_history": RunnableLambda(lambda x: x["chat_history"]),
            }
            | context_qa_prompt | self.azOpenAIllm | StrOutputParser()
        )

        self.log.info("Invoking chain for response generation")

        # Invoke the chain
        result = chain.invoke(
            {
                "question": chat_request["query"],
                "chat_history": self._get_chat_history(chat_request["chat_id"]),
            }
        )

        self.log.info("Updating chat details with new messages")

        # Update the chat history
        self._update_chat_history(chat_request["chat_id"], chat_request["query"], result)

        return result