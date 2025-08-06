from azure.storage.blob import BlobServiceClient, ContentSettings
from src.core.app_settings import get_settings
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
        
            blob = container.get_blob_client(blob_name)
            
            blob.upload_blob(
                data,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
                if content_type else None
            )
            
            # Construct URL
            account_url = self.client.primary_endpoint
            
            return f"{account_url}{container_name}/{blob_name}"
        
        except Exception as e:
            raise RuntimeError(f"Failed to upload blob: {e}")

    def list_files_in_folder(self, container_name: str, folder_name: str) -> list[str]:
        """
        Lists all file URLs in a given folder (prefix) within a container.

        :param container_name: Name of the Azure Blob Storage container.
        :param folder_name: Folder (prefix) to search within (e.g., 'myfolder/').
        :return: List of blob URLs.
        """
        try:
            container = self.client.get_container_client(container_name)
            
            # Ensure folder_name ends with a slash for prefix matching
            prefix = folder_name if folder_name.endswith('/') else folder_name + '/'
            
            blob_list = container.list_blobs(name_starts_with=prefix)
            
            account_url = self.client.primary_endpoint
            
            return [
                f"{account_url}{container_name}/{blob.name}"
                for blob in blob_list
            ]
            
        except Exception as e:
            raise RuntimeError(f"Failed to list blobs in folder: {e}")
