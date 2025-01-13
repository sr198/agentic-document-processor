# app/api/models/responses.py

from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional

class DocumentContext(BaseModel):
    text: str = Field(..., description="The relevant text chunk")
    document_type: str = Field(..., description="Type of source document")
    filename: str = Field(..., description="Source document filename")
    similarity_score: float = Field(..., description="Relevance score")

class ComponentImpact(BaseModel):
    component_id: str = Field(..., description="Component identifier")
    name: str = Field(..., description="Component name")
    affected_devices: List[str] = Field(default_factory=list, description="Affected devices")
    affected_processes: List[str] = Field(default_factory=list, description="Affected processes")
    regulatory_requirements: List[str] = Field(default_factory=list, description="Related regulatory requirements")
    
class ProcessImpact(BaseModel):
    process_id: str = Field(..., description="Process identifier")
    name: str = Field(..., description="Process name")
    affected_components: List[str] = Field(default_factory=list, description="Affected components")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Process metrics")

class RegulatoryImpact(BaseModel):
    submission_id: str = Field(..., description="Submission identifier")
    submission_type: str = Field(..., description="Type of submission")
    requirements: List[str] = Field(default_factory=list, description="Regulatory requirements")
    affected_components: List[str] = Field(default_factory=list, description="Affected components")

class ImpactAnalysisResponse(BaseModel):
    query: str = Field(..., description="Original query")
    query_type: str = Field(..., description="Type of query executed")
    component_impacts: Optional[Dict[str, ComponentImpact]] = Field(None, description="Component impact analysis")
    process_impacts: Optional[List[ProcessImpact]] = Field(None, description="Process impact analysis")
    regulatory_impacts: Optional[List[RegulatoryImpact]] = Field(None, description="Regulatory impact analysis")
    relevant_context: Optional[List[DocumentContext]] = Field(None, description="Relevant document contexts")
    summary: str = Field(..., description="Natural language summary of impacts")

class DocumentProcessingResponse(BaseModel):
    document_id: str = Field(..., description="Unique identifier for the processed document")
    document_type: str = Field(..., description="Type of document processed")
    status: str = Field(..., description="Processing status")
    entities_found: Dict[str, List[str]] = Field(..., description="Entities found in the document")
    processing_details: Dict[str, Any] = Field(..., description="Details about the processing")