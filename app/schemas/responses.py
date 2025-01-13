# app/schemas/responses.py

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuccessResponse(BaseModel):
    """Standard success response"""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ValidationError(BaseModel):
    """Validation error details"""
    field: str = Field(..., description="Field with error")
    error: str = Field(..., description="Error description")

class ValidationResponse(BaseModel):
    """Validation response"""
    is_valid: bool = Field(..., description="Validation result")
    errors: Optional[List[ValidationError]] = Field(None, description="Validation errors")