from fastapi import FastAPI, status
from src.controllers.doc_analyser_controller import router as doc_analyser_router

app = FastAPI(
    title="Document Portal API",
    description="API for document analysis and related operations.",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc" # ReDoc UI
)

# Include the doc analyser router
app.include_router(doc_analyser_router, prefix="/doc-analyser", tags=["Document Analysis"])

# Optionally, add a root endpoint
@app.get("/")
async def root():
    return {"message": "Welcome to the Document Portal API"}