import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

_BASE_PATH = Path(__file__).resolve().parent.parent.parent.parent
BASE_DIR = _BASE_PATH

class Settings(BaseSettings):
    PROJECT_NAME: str = "AUTOSAR HLD Document Analysis Assistant"
    SUBTITLE: str = "AI-Powered RAG System for Automotive Architecture Analysis"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    BASE_DIR: str = str(_BASE_PATH)
    
    # Storage & DB
    DATABASE_URL: str = f"sqlite:///{_BASE_PATH / 'data' / 'autosar.db'}"
    CHROMA_PATH: str = str(_BASE_PATH / "data" / "chroma")
    UPLOAD_DIR: str = str(_BASE_PATH / "data" / "uploads")
    PROCESSED_DIR: str = str(_BASE_PATH / "data" / "processed")
    SAMPLE_DOCS_DIR: str = str(_BASE_PATH / "data" / "sample_documents")
    
    # RAG & Embeddings
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    TOP_K: int = 5
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 100
    MAX_FILE_SIZE_MB: int = 50
    
    # LLM Configuration
    # Options: "mock" (built-in automotive expert engine), "ollama", "openai"
    LLM_PROVIDER: str = "mock"
    LLM_MODEL: str = "llama3.1"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    
    # Security
    ALLOWED_ORIGINS: list[str] = ["*"]
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.SAMPLE_DOCS_DIR, exist_ok=True)
os.makedirs(settings.CHROMA_PATH, exist_ok=True)
os.makedirs(Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent, exist_ok=True)
