# app/api/models/requests.py

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum

class QueryType(str, Enum):
    COMPONENT_USAGE = "component_usage"
    PROCESS_IMPACT = "process_impact"
    REGULATORY_IMPACT = "regulatory_impact"
    FULL_IMPACT = "full_impact"
    TIMELINE = "timeline"
    CUSTOM = "custom"

class ImpactQuery(BaseModel):
    query: str = Field(..., description="The natural language query for impact analysis")
    query_type: Optional[QueryType] = Field(None, description="Specific type of query to execute")
    include_context: bool = Field(True, description="Whether to include relevant document contexts")

class DocumentUpload(BaseModel):
    document_type: str = Field(..., description="Type of document (bom, eco, process_validation, regulatory)")
    file_path: str = Field(..., description="Path to the uploaded document")