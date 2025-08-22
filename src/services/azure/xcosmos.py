import os
import asyncio

from azure.cosmos import CosmosClient, exceptions
from src.models.doc_chat_model import DocChatModel
from src.models.view_models.documents_view_model import DocumentsViewModel 
from src.core.app_settings import get_settings
from starlette.concurrency import run_in_threadpool

class CosmosService:
    def __init__(self, container: str):
        self.settings = get_settings()
        self.client = CosmosClient.from_connection_string(self.settings.AZ_EMC_COSMOS_DB_CONNECTION_STRING)
        self.db = self.client.get_database_client(self.settings.AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME)
        self.container = self.db.get_container_client(container)

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
        
    async def add_documents(self, documents_view_model: DocumentsViewModel):
        try:
            response = await run_in_threadpool(
                self.container.create_item,
                documents_view_model
            )
            return response

        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while adding documents: {e}")