from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    Loads application configuration from environment variables or a .env file using Pydantic.
    """
    AZURE_STORAGE_CONN_STR: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_MONITOR_CONN_STR: str

    class Config:
        env_file = ".env"

def get_settings() -> Settings:
    return Settings()
