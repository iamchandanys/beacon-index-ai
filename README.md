# BEACON INDEX AI (API)

## Environment Setup

Create a `.env` file in the project root with the following fields:

```
AZURE_OPENAI_API_KEY=your-openai-api-key-here
AZURE_OPENAI_ENDPOINT=https://your-openai-endpoint-placeholder
AZURE_OPENAI_GPT_4O_FULL_ENDPOINT=https://your-gpt-4o-endpoint-placeholder
AZURE_CONTENT_SAFETY_ENDPOINT=https://your-content-safety-endpoint-placeholder
AZURE_CONTENT_SAFETY_KEY=your-content-safety-key-here
AZURE_STORAGE_CONN_STR=your-storage-connection-string-here
AZURE_MONITOR_CONN_STR=your-monitor-connection-string-here
AZ_EMC_COSMOS_DB_CONNECTION_STRING=your-cosmos-db-connection-string-here
AZ_EMC_COSMOS_DB_SITES_DATABASE_NAME=your-sites-database-name-here
AZ_EMC_COSMOS_DB_CHAT_HISTORY_CONTAINER_NAME=your-chat-history-container-name-here
```

## Running the FastAPI Application

To start the FastAPI server locally:

1. Make sure you have `uvicorn` installed:

   ```cmd
   pip install uvicorn
   ```

2. Run the FastAPI app from the project root directory:

   ```cmd
   uvicorn src.main:app --reload
   ```

3. Open your browser and go to [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) to access the Swagger UI for API testing.
