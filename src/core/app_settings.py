import os

from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    AZURE_OPENAI_API_KEY: Optional[str] = Field(default=None)
    AZURE_OPENAI_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_OPENAI_GPT_4O_MODEL: Optional[str] = Field(default=None)
    AZURE_OPENAI_GPT_4O_FULL_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_CONTENT_SAFETY_ENDPOINT: Optional[str] = Field(default=None)
    AZURE_CONTENT_SAFETY_KEY: Optional[str] = Field(default=None)
    AZURE_STORAGE_CONN_STR: Optional[str] = Field(default=None)
    AZURE_MONITOR_CONN_STR: Optional[str] = Field(default=None)
    AZ_EMC_COSMOS_DB_CONNECTION_STRING: Optional[str] = Field(default=None)
    AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME: Optional[str] = Field(default=None)
    AZ_EMC_COSMOS_DB_CHAT_HISTORY_CONTAINER_NAME: Optional[str] = Field(default=None)

def get_settings() -> Settings:
    key_vault_url = os.environ["KEY_VAULT_URL"]
    
    if not key_vault_url:
        raise ValueError("KEY_VAULT_URL environment variable is not set")

    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=key_vault_url, credential=credential)

    return Settings(
        AZURE_OPENAI_API_KEY=client.get_secret("AZURE-OPENAI-API-KEY").value,
        AZURE_OPENAI_ENDPOINT=client.get_secret("AZURE-OPENAI-ENDPOINT").value,
        AZURE_OPENAI_GPT_4O_MODEL=client.get_secret("AZURE-OPENAI-GPT-4O-MODEL").value,
        AZURE_OPENAI_GPT_4O_FULL_ENDPOINT=client.get_secret("AZURE-OPENAI-GPT-4O-FULL-ENDPOINT").value,
        AZURE_CONTENT_SAFETY_ENDPOINT=client.get_secret("AZURE-CONTENT-SAFETY-ENDPOINT").value,
        AZURE_CONTENT_SAFETY_KEY=client.get_secret("AZURE-CONTENT-SAFETY-KEY").value,
        AZURE_STORAGE_CONN_STR=client.get_secret("AZURE-STORAGE-CONN-STR").value,
        AZURE_MONITOR_CONN_STR=client.get_secret("AZURE-MONITOR-CONN-STR").value,
        AZ_EMC_COSMOS_DB_CONNECTION_STRING=client.get_secret("AZ-EMC-COSMOS-DB-CONNECTION-STRING").value,
        AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME=client.get_secret("AZ-EMC-COSMOS-DB-SITES-DATABASE-NAME").value,
        AZ_EMC_COSMOS_DB_CHAT_HISTORY_CONTAINER_NAME=client.get_secret("AZ-EMC-COSMOS-DB-CHAT-HISTORY-CONTAINER-NAME").value,
    )

if __name__ == "__main__":
    settings = get_settings()
    print(f"{settings}\n")