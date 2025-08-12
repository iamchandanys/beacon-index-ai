import os

from langchain.vectorstores import FAISS
from src.services.large_language_models.llm_service import LLMService
from langchain.schema import Document

class FaissService:
    def __init__(self):
        self.llm_service = LLMService()
        self.azOpenAIEmbeddings = self.llm_service.getAzOpenAIEmbeddings()

    def create_vector_store(self, client_id: str, product_id: str, documents: list[Document]) -> FAISS:
        """Create a FAISS vector store from the provided documents."""
        vector_store = FAISS.from_documents(documents, self.azOpenAIEmbeddings)
        
        # Save the vector store to the current working directory
        save_path = os.getcwd()
        
        # create a directory with name faiss_vector_store and add client_id and product_id directories inside it
        vector_store_dir = os.path.join(save_path, "faiss_vector_store", client_id, product_id)
        
        # create directory if it does not exist
        os.makedirs(vector_store_dir, exist_ok=True)

        vector_store.save_local(vector_store_dir)
        
        return vector_store

    def load_vector_store(self, client_id: str, product_id: str) -> FAISS:
        """Load a FAISS vector store from a file."""
        vector_store_dir = os.path.join("faiss_vector_store", client_id, product_id)
        
        vector_store = FAISS.load_local(vector_store_dir, self.azOpenAIEmbeddings, allow_dangerous_deserialization=True)
        
        return vector_store