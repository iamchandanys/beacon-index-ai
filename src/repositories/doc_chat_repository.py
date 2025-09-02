import uuid
import structlog

from fastapi import UploadFile, File
from langchain.schema import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from src.services.azure.blob import BlobService
from src.services.llm.providers import LLMService
from src.services.vectorstores.faiss_store import FaissService
from src.services.azure.cosmos import CosmosService
from src.models.requests import ChatRequest
from src.models.view_models.documents_view_model import DocumentsViewModel
from src.models.view_models.chat_history_view_model import ChatHistoryViewModel
from src.services.prompts.prompting import contextualize_question_prompt, context_qa_prompt
from src.services.evaluate.deepeval_evaluate import DeepevalEvaluate

class DocChatRepository:
    def __init__(self):
        self.log = structlog.get_logger(self.__class__.__name__)
        self.blob_service = BlobService()
        self.cosmos_service = CosmosService()
        self.llm_service = LLMService()
        self.faiss_service = FaissService()
        self.azOpenAIllm = self.llm_service.getAzOpenAIllm()
        self.deepeval = DeepevalEvaluate()
    
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
        # Validate input
        if not client_id or not product_id:
            self.log.error("Client ID or Product ID is not provided")
            raise ValueError("Client ID and Product ID must be provided.")
        
        # Query documents from Cosmos DB
        documents: list[DocumentsViewModel] = list(
            await self.cosmos_service.query_items_async(
                "documents",
                "SELECT * FROM c WHERE c.client_id = @client_id AND c.product_id = @product_id",
                [
                    {"name": "@client_id", "value": client_id},
                    {"name": "@product_id", "value": product_id}
                ]
            )
        )
        
        if len(documents) > 1:
            self.log.error("Multiple document records found which should not happen.", client_id=client_id, product_id=product_id)
            raise ValueError("Multiple document records found which should not happen.")
        
        self.log.info("Vectorizing documents", client_id=client_id, product_id=product_id)

        faiss_service = FaissService()
        faiss_service.create_vector_store(
            client_id, product_id, 
            documents=[Document(page_content=doc["page_content"], metadata=doc["metadata"]) for doc in documents[0]["chunked_documents"]]
        )

        self.log.info("Vector store created successfully", client_id=client_id, product_id=product_id)

    async def _init_chat(self, client_id: str, product_id: str) -> ChatHistoryViewModel:
        self.log.info("Initializing new chat", client_id=client_id, product_id=product_id)

        doc_chat_model = ChatHistoryViewModel(client_id=client_id, product_id=product_id)

        chat_details_dict = await self.cosmos_service.create_item_async("chat-history", doc_chat_model.model_dump())

        chat_details = ChatHistoryViewModel(**chat_details_dict)

        self.log.info("Chat initialized successfully", chat_id=doc_chat_model.id)

        return chat_details

    @staticmethod
    def _format_docs(docs: list[Document]) -> str:
        return "\n\n".join([doc.page_content for doc in docs])

    async def _get_chat_history(self, chat_id: str) -> list[AIMessage | HumanMessage | SystemMessage]:
        self.log.info("Fetching chat details", chat_id=chat_id)
        
        chat_history: list[AIMessage | HumanMessage | SystemMessage] = []

        result = list(
            await self.cosmos_service.query_items_async(
                "chat-history",
                "SELECT * FROM c WHERE c.id = @chat_id",
                [
                    {"name": "@chat_id", "value": chat_id}
                ]
            )
        )

        if len(result) == 0:
            self.log.error("No chat history found for the given chat_id", chat_id=chat_id)
            return chat_history

        chat_details: ChatHistoryViewModel = ChatHistoryViewModel(**result[0])

        for message in chat_details.messages:
            for content in message.content:
                if message.role == "system":
                    chat_history.append(SystemMessage(content.text))
                elif message.role == "user":
                    chat_history.append(HumanMessage(content.text))
                elif message.role == "assistant":
                    chat_history.append(AIMessage(content.text))

        self.log.info("Chat history fetched successfully", chat_id=chat_id, history_length=len(chat_history))
        
        return chat_history
    
    async def _update_chat_history(self, chat_id: str, user_message: str, assistant_message: str) -> None:
        self.log.info("Updating chat history", chat_id=chat_id)

        results = list(
            await self.cosmos_service.query_items_async(
                "chat-history",
                "SELECT * FROM c WHERE c.id = @chat_id",
                [
                    {"name": "@chat_id", "value": chat_id}
                ]
            )
        )
        
        if not results:
            self.log.error("No chat history found for the given chat_id", chat_id=chat_id)
            raise ValueError(f"No chat history found for the given chat_id: {chat_id}")

        chat_details = ChatHistoryViewModel(**results[0])

        # Append user message
        chat_details.messages.append({
            "role": "user",
            "content": [{"text": user_message, "type": "text", "tokensUsed": 0}]
        })

        # Append assistant message
        chat_details.messages.append({
            "role": "assistant",
            "content": [{"text": assistant_message, "type": "text", "tokensUsed": 0}]
        })

        await self.cosmos_service.update_item_async("chat-history", chat_details.model_dump())

        self.log.info("Chat history updated successfully", chat_id=chat_id, messages_count=len(chat_details.messages))
    
    # Todo: Log to file only in local
    def _log_prompt(self, prompt, prompt_type: str = "text"):
        # save_path = os.getcwd()
        # vector_store_dir = os.path.join(save_path, "prompt_logging")
        # os.makedirs(vector_store_dir, exist_ok=True)
        
        # # Create a unique filename for each log
        # log_filename = f"prompt_log_{prompt_type}_{uuid.uuid4().hex}.txt"
        # log_filepath = os.path.join(vector_store_dir, log_filename)
        
        # with open(log_filepath, "w", encoding="utf-8") as f:
        #     if hasattr(prompt, "messages"):
        #         for msg in prompt.messages:
        #             f.write(f"{type(msg).__name__}: {msg.content}\n")
        #             f.write("----------------------------\n")
        #     else:
        #         f.write(str(prompt) + "\n")
        #         f.write("----------------------------\n")

        return prompt
    
    async def chat(self, chat_request: ChatRequest) -> dict:
        # If chat_id is not present, initialize a new chat
        if not chat_request.get("chat_id"):
            self.log.info("No chat_id provided, initializing a new chat")
            chat_details = await self._init_chat(chat_request["client_id"], chat_request["product_id"])
            chat_request["chat_id"] = chat_details.id
            self.log.info("New chat initialized", chat_id=chat_request["chat_id"])
        
        # Load the vector store
        self.log.info("Loading vector store...")
        vector_store = self.faiss_service.load_vector_store(chat_request["client_id"], chat_request["product_id"])
        self.log.info("Vector store loaded successfully")

        # Create retriever from vector store
        self.log.info("Creating retriever from vector store...")
        retriever = vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        self.log.info("Retriever created successfully")
        
        self.log.info("Fetching conversation history")
        conversation_history = await self._get_chat_history(chat_request["chat_id"])
        self.log.info("Conversation history fetched successfully")

        self.log.info("Preparing question rewriter and retrieval chain")

        # Rewrite user question with chat history context
        question_rewriter = (
            {
                "input": RunnableLambda(lambda x: x["question"]), 
                "chat_history": RunnableLambda(lambda x: x["chat_history"])
            }
            | contextualize_question_prompt 
            | RunnableLambda(lambda prompt: self._log_prompt(prompt, prompt_type="contextualize_question_prompt"))
            | self.azOpenAIllm 
            | StrOutputParser()
        )

        # Retrieve docs for rewritten question
        retrieve_docs = (
            {
                "question": question_rewriter,
                "chat_history": RunnableLambda(lambda x: x["chat_history"])
            }
            | RunnableLambda(lambda x: self._log_prompt(x["question"], prompt_type="rewritten_question"))
            | retriever
            | self._format_docs
        )

        # Answer using retrieved docs + original input + chat history
        chain = (
            {
                "context": retrieve_docs,
                "input": RunnableLambda(lambda x: x["question"]),
                "chat_history": RunnableLambda(lambda x: x["chat_history"]),
            }
            | context_qa_prompt
            | RunnableLambda(lambda prompt: self._log_prompt(prompt, prompt_type="context_qa_prompt"))
            | self.azOpenAIllm
            | StrOutputParser()
        )
        
        self.log.info("Invoking chain for response generation")

        # Invoke the chain
        result = chain.invoke(
            {
                "question": chat_request["query"],
                "chat_history": conversation_history,
            }
        )

        # Evaluate response
        self.log.info("Evaluating the response")
        retrieved_docs = retrieve_docs.invoke({
            "question": chat_request["query"],
            "chat_history": conversation_history,
        })
        self.deepeval.evaluate(chat_request["query"], result, None, [retrieved_docs])
        self.log.info("Response evaluated successfully")

        # Update the chat history
        self.log.info("Updating chat details with new messages")
        await self._update_chat_history(chat_request["chat_id"], chat_request["query"], result)
        self.log.info("Chat details updated successfully")

        return {
            "response": result,
            "chatId": chat_request["chat_id"]
        }