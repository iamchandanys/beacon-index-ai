import importlib.metadata

packages = [
    "pydantic",
    "pydantic-settings",
    "setuptools",
    "python-dotenv",
    "ipykernel",
    "langchain",
    "langchain-community",
    "langchain-groq",
    "langchain-google-genai",
    "langchain-openai",
    "pypdf",
    "faiss-cpu",
    "structlog",
    "PyMuPDF",
    "pdfplumber",
    "FastAPI",
    "uvicorn",
    "python-multipart",
    "azure-storage-blob",
    "opencensus-ext-azure",
    "azure-cosmos",
    "azure-identity",
    "azure-keyvault-secrets",
    "docling",
    "torch",
    "torchvision",
    "torchaudio",
    "pytest",
    "deepeval"
]

for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} (not installed)")