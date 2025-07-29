from azure.storage.blob import BlobServiceClient, ContentSettings
from src.core.config import get_settings
from typing import BinaryIO

class BlobService:
    def __init__(self):
        settings = get_settings()
        self.client = BlobServiceClient.from_connection_string(
            settings.AZURE_STORAGE_CONN_STR
        )
        
    def upload_stream(self, container_name: str, blob_name: str, data: BinaryIO, content_type: str = None) -> str:
        """
        Uploads a file-like stream to Azure Blob Storage.
        
        :param container_name: Name of the Azure Blob Storage container.
        :param blob_name: Name of the blob (file) to be created.
        :param data: File-like object containing the document data.
        :param content_type: MIME type of the document.
        :return: URL of the uploaded document.
        """
        
        try:
            
            container = self.client.get_container_client(container_name)
        
            # Create the container if it does not exist
            try:
                container.create_container()
            except Exception:
                pass  # container likely exists

            blob = container.get_blob_client(blob_name)
            
            blob.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
                if content_type else None
            )
            
            # Construct URL
            account_url = self.client.primary_endpoint
            return f"{account_url}/{container_name}/{blob_name}"
        
        except Exception as e:
            
            raise RuntimeError(f"Failed to upload blob: {e}")
