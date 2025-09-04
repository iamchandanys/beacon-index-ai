# Beacon Index AI (API) 🚀

## 🌐 Live URLs

- Frontend: [https://beaconai.azurewebsites.net/cw](https://beaconai.azurewebsites.net/cw?cid=d6b607aa-578f-4916-90fa-e2358f366726&pid=15f4193d-1ae5-45b2-8cc3-4a82ac311903)
- Backend Swagger: [https://beacon-index-ai.azurewebsites.net/docs](https://beacon-index-ai.azurewebsites.net/docs)

## 📋 Assignment

- ✅ Enable the project for every document format (.ppt, .docx, .md, .txt, .pdf, .xlsx, .csv) - **Done**
- ✅ Add code for handling table and image data. - **Done**
- ✅ Integrate an evaluation matrix using DeepEval. - **Done**
- ✅ Write at least 10 test cases and ensure these test cases are validated before and after each commit. - **Done**
- ✅ Implement LangChain In-Memory Cache inside the project. - **Done**

## 📁 Project Structure & Key Files

### 🏁 Main Entrypoint

- [**src/main.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/main.py) 🚦  
   FastAPI app setup, routing, CORS, logging, and admin endpoints.

### ⚙️ Core Configuration

- [**src/core/app_settings.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/core/app_settings.py) 🔑  
   Loads secrets from Azure Key Vault & environment variables.
- [**src/core/config.yaml**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/core/config.yaml) 📝  
   Contains non-secret configuration values. Secrets and sensitive settings are managed separately via Azure Key Vault.
- [**.env**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/.env) 🌱  
   Local environment variables for dev/test.

### 🧠 LLM & Vector Stores

- [**src/services/llm/providers.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/llm/providers.py) 🤖  
   Azure OpenAI LLM and embeddings setup.
- [**src/services/vectorstores/faiss_store.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/vectorstores/faiss_store.py) 🗄️  
   FAISS-based vector store for semantic search.

### 🧩 Document Processing

- [**src/services/extractors/docling_file_extractor.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/extractors/docling_file_extractor.py) 📑  
   Uses Docling from IBM research for advanced PDF/document chunking.
- [**src/services/extractors/pdf_chunker.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/extractors/pdf_chunker.py) ✂️  
   PDF chunking and table extraction utility.

### ☁️ Azure Integrations

- [**src/services/azure/blob.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/azure/blob.py) 🗂️  
   Azure Blob Storage upload/listing.
- [**src/services/azure/cosmos.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/azure/cosmos.py) 🪐  
   Cosmos DB async CRUD operations.

### 📝 Prompts & Utils

- [**src/services/prompts/prompting.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/services/prompts/prompting.py) 🗣️  
   Prompt templates for LLM and chat.
- [**src/utils/az_logger.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/utils/az_logger.py) 📊  
   Structured logging to Azure Monitor.
- [**src/utils/custom_exception.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/src/utils/custom_exception.py) 🚨  
   Custom error handling for better debugging.

### 🧪 Testing

- [**tests/test_basics.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/tests/test_basics.py) 🧪  
   Basic API endpoint tests using FastAPI’s test client.

### 🛠️ Setup & Dependencies

- [**requirements.txt**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/requirements.txt) 📦  
   Main Python dependencies.
- [**requirements-heavy.txt**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/requirements-heavy.txt) 🏋️  
   Extra dependencies for local GPU/dev (Docling, Torch).
- [**setup.py**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/setup.py) 🛠️  
   Python package setup.
- [**Dockerfile**](https://github.com/iamchandanys/beacon-index-ai/blob/dev/Dockerfile) 🐳  
   Containerization for deployment.

---

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

#### Running Tests

To run all tests using pytest, use the following command in your project root:

```cmd
pytest -q
```

The `-q` flag runs pytest in quiet mode, showing only minimal output (just test results).
