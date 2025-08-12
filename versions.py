import importlib.metadata

packages = [
    "pydantic",
    "pydantic_settings",
    "setuptools",
    "python-dotenv",
    "ipykernel",
    "langchain",
    "langchain_community",
    "langchain_groq",
    "langchain_google_genai",
    "langchain_openai",
    "pypdf",
    "faiss-cpu",
    "structlog",
    "PyMuPDF",
    "FastAPI",
    "uvicorn",
    "python-multipart",
    "azure-storage-blob",
    "opencensus-ext-azure",
    "azure-cosmos"
]

for pkg in packages:
    try:
        version = importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} (not installed)")