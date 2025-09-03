import uuid
import structlog

from typing import List, Optional
from langgraph.store.memory import InMemoryStore
from langchain.embeddings import init_embeddings
from src.utils.get_configs import GetConfigs
from src.core.app_settings import get_settings

user_memory = [
    {
        "user_id": "ffcfb843-e07c-4c27-878a-007c7d79b2b9",
        "memories": [
            "User's name is Chandan",
            "User's favorite color is blue",
            "User's favorite food is pizza"
        ]
    }
]

class UserMemory:
    """
    Handles user memory storage and retrieval using LangGraph and embeddings.
    """
    def __init__(self, user_id: str) -> None:
        """
        Initialize LangGraphMemory for a user.
        Args:
            user_id (str): Unique user identifier.
        """
        self.log = structlog.get_logger(self.__class__.__name__)
        self.configs = GetConfigs().get_configs()
        self.settings = get_settings()
        self.user_id = user_id
        self.namespace = (user_id, "memories")
        self.store: Optional[InMemoryStore] = None
        self._store_in_memory()

    def _get_user_memories(self, user_id: str) -> List[str]:
        """
        Retrieve list of memories for a user.
        Args:
            user_id (str): Unique user identifier.
        Returns:
            List[str]: List of memory strings.
        """
        user = next((u for u in user_memory if u["user_id"] == user_id), None)
        return user["memories"] if user else []

    def _store_in_memory(self) -> None:
        """
        Store user memories in the in-memory vector store.
        """
        try:
            model_name = self.configs['az_open_ai_embeddings']['model_name']
            
            embeddings = init_embeddings(
                f"azure_openai:{model_name}",
                openai_api_key=self.settings.AZURE_OPENAI_API_KEY,
                azure_endpoint=self.settings.AZURE_OPENAI_ENDPOINT
            )
            
            store = InMemoryStore(
                index={
                    "embed": embeddings,
                    "dims": 1536,
                }
            )
            
            user_memories = self._get_user_memories(self.user_id)
            
            for memory in user_memories:
                store.put(self.namespace, str(uuid.uuid4()), {"text": memory})
                
            self.store = store
            
        except Exception as e:
            self.log.error(f"Error initializing memory store: {e}")
            self.store = None

    def retrieve_memories(self, query: str, top_k: int = 5) -> str:
        """
        Retrieve top_k memories matching the query.
        Args:
            query (str): Search query.
            top_k (int): Number of top results to return.
        Returns:
            str: Concatenated memory strings.
        """
        if not self.store:
            self.log.warning("Memory store not initialized.")
            return ""
        
        try:
            memories = self.store.search(self.namespace, query=query, limit=top_k)
            return "\n".join(memory.value['text'] for memory in memories)
        
        except Exception as e:
            self.log.error(f"Error retrieving memories: {e}")
            return ""