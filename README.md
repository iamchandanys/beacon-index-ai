# llmops-workshop-document-portal

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
