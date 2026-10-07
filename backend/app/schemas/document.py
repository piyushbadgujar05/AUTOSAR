from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class DocumentBase(BaseModel):
    name: str
    project: str = "ADAS Control System"
    version: str = "1.0"
    document_type: str = "High-Level Design"
    description: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    file_path: str
    upload_date: datetime
    status: str
    total_pages: int
    chunk_count: int
    file_size: int
    file_hash: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ChunkResponse(BaseModel):
    id: int
    document_id: str
    page_number: int
    section: str
    content: str
    chunk_id: str

    model_config = ConfigDict(from_attributes=True)

