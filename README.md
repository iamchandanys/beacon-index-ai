# llmops-workshop-document-portal

## Environment Setup

Create a `.env` file in the project root with the following fields:

```
AZURE_STORAGE_CONN_STR=your-azure-storage-connection-string
AZURE_OPENAI_API_KEY=your-azure-openai-api-key
AZURE_OPENAI_ENDPOINT=your-azure-openai-endpoint
AZURE_MONITOR_CONN_STR=your-azure-monitor-connection-string
```

## Key Utility Modules

- [`az_logger`](src/utils/az_logger.py) – Azure Monitor and console logging setup.
- [`custom_exception`](src/utils/custom_exception.py) – Custom exception class for detailed error reporting.
- [`azure_blob_storage.blob_service`](src/services/azure_blob_storage/blob_service.py) – Azure Blob Storage upload service.

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
