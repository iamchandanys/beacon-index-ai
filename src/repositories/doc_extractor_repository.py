import os
import structlog

from src.models.view_models.documents_view_model import DocumentsViewModel, CustomDocument
from src.services.extractors.docling_file_extractor import DoclingFileExtractor
from src.services.azure.blob import BlobService
from src.services.azure.cosmos import CosmosService

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

class DocExtractorRepository:
    def __init__(self):
        self.log = structlog.get_logger(self.__class__.__name__)
        self.blob_service = BlobService()
        self.cosmos_service = CosmosService()
    
    async def sync_documents(self, client_id: str, product_id: str) -> None:
        # Validate input
        if not client_id or not product_id:
            self.log.error("Client ID or Product ID is not provided")
            raise ValueError("Client ID and Product ID must be provided.")

        # List files from blob storage
        file_urls = self.blob_service.list_files_in_folder("document-chat", f"{client_id}/{product_id}/") # Todo: Make list_files_in_folder async
        
        if not file_urls:
            self.log.error("No files found in blob storage", client_id=client_id, product_id=product_id)
            raise ValueError(f"No files found for client_id '{client_id}' and product_id '{product_id}' in blob storage.")

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

        docling_file_extractor = DoclingFileExtractor()
        custom_documents: list[CustomDocument] = []

        # Chunk files
        for url in file_urls:
            custom_documents.extend(docling_file_extractor.chunk_file(url)) # Todo: Make chunk_file async

        # Create or update document record
        if len(documents) == 0:
            self.log.info("Creating new document record", client_id=client_id, product_id=product_id)
            
            documents_view_model = DocumentsViewModel(
                client_id=client_id,
                product_id=product_id,
                chunked_documents=custom_documents
            )
            
            await self.cosmos_service.create_item_async("documents", documents_view_model.model_dump())
            
            self.log.info("Document record created successfully", client_id=client_id, product_id=product_id)
        else:
            self.log.info("Updating existing document record", client_id=client_id, product_id=product_id)
            
            document = documents[0]
            document["chunked_documents"] = [doc.model_dump() for doc in custom_documents]

            await self.cosmos_service.update_item_async("documents", document)
            
            self.log.info("Document record updated successfully", client_id=client_id, product_id=product_id)