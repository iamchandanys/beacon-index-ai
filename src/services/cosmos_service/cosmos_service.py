import os

from azure.cosmos import CosmosClient, exceptions
from src.models.doc_chat_model import DocChatModel
from src.core.app_settings import get_settings

class CosmosService:
    def __init__(self):
        self.settings = get_settings()
        self.client = CosmosClient.from_connection_string(self.settings.AZ_EMC_COSMOS_DB_CONNECTION_STRING)
        self.db = self.client.get_database_client(self.settings.AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME)
        self.container = self.db.get_container_client(self.settings.AZ_EMC_COSMOS_DB_CHAT_HISTORY_CONTAINER_NAME)

    def init_chat(self, chat_state: DocChatModel) -> DocChatModel:
        """
        Initialize a new chat in the Cosmos DB.
        :param chat_state: DocChatModel object containing chat details.
        :return: The created chat state with its ID.
        """
        try:
            response = self.container.create_item(
                body=chat_state,
            )
            return response
        
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while creating the chat: {e}")

    def get_chat(self, id: str) -> DocChatModel:
        """
        Retrieve a chat by its ID from the Cosmos DB.
        :param id: The ID of the chat to retrieve.
        
        :return: DocChatModel object if found, None otherwise.
        """
        try:
            response = self.container.read_item(
                item=id,
                partition_key=[id]
            )
            return response
        
        except exceptions.CosmosResourceNotFoundError:
            raise RuntimeError(f"Chat with ID {id} not found.")
        
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while retrieving the chat: {e}")

    def update_chat(self, chat_state: DocChatModel):
        """
        Update an existing chat in the Cosmos DB.
        :param chat_state: DocChatModel object containing updated chat details.
        :return: The updated chat state if successful, None otherwise.
        """
        try:
            response = self.container.upsert_item(
                body=chat_state
            )
            return response
        
        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while updating the chat: {e}")