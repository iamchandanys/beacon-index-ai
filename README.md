# Beacon Index AI (API) 🚀

## 📁 Project Structure & Key Files

### 🏁 Main Entrypoint

- **`src/main.py`** 🚦  
   FastAPI app setup, routing, CORS, logging, and admin endpoints.

### ⚙️ Core Configuration

- **`src/core/app_settings.py`** 🔑  
   Loads secrets from Azure Key Vault & environment variables.
- **`src/core/config.yaml`** 📝  
   Contains non-secret configuration values.
  Secrets and sensitive settings are managed separately via Azure Key Vault.
- **`.env`** 🌱  
   Local environment variables for dev/test.

### 🧠 LLM & Vector Stores

- **`src/services/llm/providers.py`** 🤖  
   Azure OpenAI LLM and embeddings setup.
- **`src/services/vectorstores/faiss_store.py`** 🗄️  
   FAISS-based vector store for semantic search.

### 🧩 Document Processing

- **`src/services/extractors/docling_file_extractor.py`** 📑  
   Uses Docling from IBM research for advanced PDF/document chunking.
- **`src/services/extractors/pdf_chunker.py`** ✂️  
   PDF chunking and table extraction utility.

### ☁️ Azure Integrations

- **`src/services/azure/blob.py`** 🗂️  
   Azure Blob Storage upload/listing.
- **`src/services/azure/cosmos.py`** 🪐  
   Cosmos DB async CRUD operations.

### 📝 Prompts & Utils

- **`src/services/prompts/prompting.py`** 🗣️  
   Prompt templates for LLM and chat.
- **`src/utils/az_logger.py`** 📊  
   Structured logging to Azure Monitor.
- **`src/utils/custom_exception.py`** 🚨  
   Custom error handling for better debugging.

### 🧪 Testing

- **`tests/test_basics.py`** 🧪  
   Basic API endpoint tests using FastAPI’s test client.

### 🛠️ Setup & Dependencies

- **`requirements.txt`** 📦  
   Main Python dependencies.
- **`requirements-heavy.txt`** 🏋️  
   Extra dependencies for local GPU/dev (Docling, Torch).
- **`setup.py`** 🛠️  
   Python package setup.
- **`Dockerfile`** 🐳  
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
