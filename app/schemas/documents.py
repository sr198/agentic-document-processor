# app/schemas/documents.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class DocumentMetadata(BaseModel):
    """Base metadata for all documents"""
    document_id: str = Field(..., description="Unique document identifier")
    filename: str = Field(..., description="Original filename")
    document_type: str = Field(..., description="Type of document")
    processed_at: datetime = Field(..., description="Processing timestamp")
    version: Optional[str] = Field(None, description="Document version")

class DocumentContent(BaseModel):
    """Base content for all documents"""
    raw_text: str = Field(..., description="Raw document text")
    structured_data: Dict[str, Any] = Field(..., description="Structured content")
    relationships: List[Dict[str, str]] = Field(..., description="Extracted relationships")
    embeddings: Optional[List[List[float]]] = Field(None, description="Text chunk embeddings")

class ProcessedDocument(BaseModel):
    """Complete processed document"""
    metadata: DocumentMetadata
    content: DocumentContent