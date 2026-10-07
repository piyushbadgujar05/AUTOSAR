from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.models import init_db
from backend.app.api.health import router as health_router
from backend.app.api.documents import router as documents_router
from backend.app.api.chat import router as chat_router
from backend.app.api.architecture import router as architecture_router
from backend.app.api.analysis import router as analysis_router
from backend.app.api.comparison import router as comparison_router
from backend.app.api.reports import router as reports_router

# Initialize database
init_db()
logger.info("Database initialized successfully.")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Powered RAG System for Automotive Architecture Analysis (AUTOSAR HLD)",
    version=settings.VERSION
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.app.schemas.chat import DebugRetrievalRequest, DebugRetrievalResponse
from backend.app.api.chat import debug_retrieval_endpoint

# Include Routers
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(chat_router, prefix=settings.API_PREFIX)
app.include_router(architecture_router, prefix=settings.API_PREFIX)
app.include_router(analysis_router, prefix=settings.API_PREFIX)
app.include_router(comparison_router, prefix=settings.API_PREFIX)
app.include_router(reports_router, prefix=settings.API_PREFIX)

@app.post("/debug/retrieval", response_model=DebugRetrievalResponse, tags=["Debug"])
def root_debug_retrieval(req: DebugRetrievalRequest):
    """Direct root debug retrieval endpoint (Requirement 17)."""
    return debug_retrieval_endpoint(req)

@app.get("/")
def root():
    return {
        "title": settings.PROJECT_NAME,
        "subtitle": settings.SUBTITLE,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "health_check": f"{settings.API_PREFIX}/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
