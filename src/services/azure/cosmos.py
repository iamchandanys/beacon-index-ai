from azure.cosmos import CosmosClient, exceptions
from src.core.app_settings import get_settings
from starlette.concurrency import run_in_threadpool

class Cosmos:
    def __init__(self, container):
        self.settings = get_settings()
        self.client = CosmosClient.from_connection_string(self.settings.AZ_EMC_COSMOS_DB_CONNECTION_STRING)
        self.db = self.client.get_database_client(self.settings.AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME)
        self.container = self.db.get_container_client(container)

    async def _create_item_sync(self, item):
        try:
            response = await run_in_threadpool(
                self.container.create_item,
                item
            )
            return response

        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while adding documents: {e}")
