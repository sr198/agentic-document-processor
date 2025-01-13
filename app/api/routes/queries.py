# app/api/routes/queries.py

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from ..models.requests import ImpactQuery, DocumentUpload
from ..models.responses import ImpactAnalysisResponse, DocumentProcessingResponse
from ...core.query_engine import ImpactQueryEngine
from ...core.document_processor import DocumentProcessor
from ...core.graph_manager import GraphManager
from loguru import logger
import tempfile
import os
import uuid
from typing import Dict

router = APIRouter()
graph_manager = GraphManager()
query_engine = ImpactQueryEngine(graph_manager)
document_processor = DocumentProcessor()

@router.post("/impact-analysis", response_model=ImpactAnalysisResponse)
async def analyze_impact(query: ImpactQuery):
    """Execute an impact analysis query"""
    try:
        # Execute query
        result = await query_engine.execute_query(
            query=query.query,
            query_type=query.query_type if query.query_type else None
        )
        
        # Transform to response model
        response = ImpactAnalysisResponse(
            query=query.query,
            query_type=result['query_type'],
            summary=result.get('analysis', 'No summary available')
        )
        
        # Add impacts based on query type
        if 'component_impacts' in result:
            response.component_impacts = {
                component_id: ComponentImpact(**impact_data)
                for component_id, impact_data in result['component_impacts'].items()
            }
            
        if 'process_impacts' in result:
            response.process_impacts = [
                ProcessImpact(**impact_data)
                for impact_data in result['process_impacts']
            ]
            
        if 'regulatory_impacts' in result:
            response.regulatory_impacts = [
                RegulatoryImpact(**impact_data)
                for impact_data in result['regulatory_impacts']
            ]
            
        # Add context if requested
        if query.include_context and 'relevant_context' in result:
            response.relevant_context = [
                DocumentContext(**context)
                for context in result['relevant_context']
            ]
        
        return response
        
    except Exception as e:
        logger.error(f"Error processing impact analysis query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

@router.post("/documents/upload", response_model=DocumentProcessingResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = None
):
    """Upload and process a new document"""
    try:
        # Generate unique ID for this document
        document_id = str(uuid.uuid4())
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        
        # Schedule document processing
        background_tasks.add_task(
            process_document,
            document_id,
            temp_path,
            file.filename,
            document_type
        )
        
        return DocumentProcessingResponse(
            document_id=document_id,
            document_type=document_type or "auto-detected",
            status="processing",
            entities_found={},
            processing_details={
                "original_filename": file.filename,
                "size": len(content)
            }
        )
        
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        if 'temp_path' in locals():
            os.unlink(temp_path)
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading document: {str(e)}"
        )

@router.get("/documents/{document_id}", response_model=DocumentProcessingResponse)
async def get_document_status(document_id: str):
    """Get status of document processing"""
    try:
        # Here you would typically check a document processing status store
        # For now, we'll return a mock response
        return DocumentProcessingResponse(
            document_id=document_id,
            document_type="unknown",
            status="pending",
            entities_found={},
            processing_details={}
        )
        
    except Exception as e:
        logger.error(f"Error getting document status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error getting document status: {str(e)}"
        )

async def process_document(
    document_id: str,
    file_path: str,
    original_filename: str,
    document_type: str = None
):
    """Background task to process uploaded document"""
    try:
        # Process document
        processed_data = await document_processor.process_document(file_path)
        
        # Store in graph database
        await graph_manager.store_processed_document(processed_data)
        
        # Clean up temporary file
        os.unlink(file_path)
        
        # Here you would typically update a document processing status store
        
    except Exception as e:
        logger.error(f"Error processing document {document_id}: {str(e)}")
        # Here you would typically update status store with error
        if os.path.exists(file_path):
            os.unlink(file_path)