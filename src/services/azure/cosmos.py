from azure.cosmos import CosmosClient, exceptions
from src.core.app_settings import get_settings
from starlette.concurrency import run_in_threadpool

class CosmosService:
    def __init__(self):
        self.settings = get_settings()
        self.client = CosmosClient.from_connection_string(self.settings.AZ_EMC_COSMOS_DB_CONNECTION_STRING)
        self.db = self.client.get_database_client(self.settings.AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME)
        # self.container = self.db.get_container_client(container)

    async def create_item_async(self, container_name, item: dict):
        try:
            response = await run_in_threadpool(
                self.db.get_container_client(container_name).create_item,
                item
            )
            return response

        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while adding documents: {e}")

    async def query_items_async(self, container_name, query: str, parameters: list[dict]):
        try:
            response = await run_in_threadpool(
                self.db.get_container_client(container_name).query_items,
                query,
                parameters
            )
            return response

        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while querying documents: {e}")
        
    async def update_item_async(self, container_name, item: dict):
        try:
            response = await run_in_threadpool(
                self.db.get_container_client(container_name).upsert_item,
                item
            )
            return response

        except exceptions.CosmosHttpResponseError as e:
            raise RuntimeError(f"An error occurred while updating documents: {e}")

# For testing purposes
if __name__ == "__main__":
    import uuid
    import asyncio
    from src.models.view_models.documents_view_model import DocumentsViewModel
    
    doc_view_model = DocumentsViewModel(client_id=str(uuid.uuid4()), product_id=str(uuid.uuid4()))
    
    cosmos = CosmosService()
    
    async def main():
        await cosmos.create_item_async("documents", doc_view_model.model_dump())

        result = await cosmos.query_items_async(
            "documents",
            "SELECT * FROM c WHERE c.client_id = @client_id AND c.product_id = @product_id",
            [
                {"name": "@client_id", "value": doc_view_model.client_id},
                {"name": "@product_id", "value": doc_view_model.product_id}
            ]
        )
        
        print(list(result))
        
        doc_view_model.modified_at = "2024-01-01T00:00:00Z"

        await cosmos.update_item_async("documents", doc_view_model.model_dump())

    asyncio.run(main())