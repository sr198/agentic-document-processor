# tests/test_document_processor.py
from dotenv import load_dotenv
load_dotenv()  # Add this at the top

import pytest
from pathlib import Path
import pandas as pd
from unittest.mock import patch, Mock
from app.core.document_processor import DocumentProcessor
from app.core.config import Settings

# Mock settings for testing
@pytest.fixture
def mock_settings():
    return Settings(
        OPENAI_API_KEY="test-key",
        NEO4J_PASSWORD="test-password",
        LLAMAPARSE_API_KEY="test-key"
    )

# Mock configuration for testing
@pytest.fixture
def mock_config():
    return {
        "document_families": {
            "bom": {
                "patterns": ["*_BOM*.csv", "*BillOfMaterials*.csv"],
                "type": "structured",
                "extract_settings": {
                    "relationships": [
                        {
                            "type": "USED_IN",
                            "source_field": "Component ID",
                            "target_field": "Device Name"
                        }
                    ]
                }
            },
            "eco": {
                "patterns": ["*_ECO*.docx", "*_ChangeOrder*.pdf"],
                "type": "unstructured",
                "parser_settings": {
                    "sections": ["Change Details", "Justification"]
                },
                "extract_settings": {
                    "entities": [
                        {
                            "name": "component",
                            "pattern": "CMP-\\d{4}"
                        }
                    ]
                }
            }
        }
    }

@pytest.fixture
def document_processor(mock_settings, mock_config):
    with patch('app.core.document_processor.get_settings', return_value=mock_settings), \
         patch('app.core.document_processor.get_document_config', return_value=mock_config):
        processor = DocumentProcessor()
        return processor

@pytest.fixture
def sample_bom():
    content = """Component ID,Component Name,Device Name,Version,Supplier Name
CMP-1001,Control Unit,GlucoMonitor Pro 2000,v1.2,BioCore Tech"""
    path = Path("test_bom.csv")
    path.write_text(content)
    yield path
    path.unlink()

@pytest.mark.asyncio
async def test_process_structured_document(document_processor, sample_bom):
    # Mock embedding generation
    with patch.object(document_processor, '_generate_embeddings', 
                     return_value=[[0.1] * 1536]):
        result = await document_processor.process_document(str(sample_bom))
        
        assert result['family'] == 'bom'
        assert len(result['content']['structured_data']) == 1
        assert result['content']['structured_data'][0]['Component ID'] == 'CMP-1001'
        assert len(result['embeddings']) == len(result['content']['text_chunks'])

def test_identify_document_family(document_processor):
    assert document_processor.identify_document_family("test_BOM_123.csv") == "bom"
    assert document_processor.identify_document_family("ECO_20250111.docx") == "eco"
    assert document_processor.identify_document_family("invalid.txt") is None

@pytest.mark.asyncio
async def test_process_unstructured_document(document_processor):
    # Create a sample ECO document
    content = """# Change Details
Component Affected: CMP-2002 (Adhesive Strip)

# Justification
Customer complaints of allergic reactions."""
    
    path = Path("test_ECO.docx")
    path.write_text(content)
    
    try:
        # Mock LlamaParse and embedding generation
        with patch.object(document_processor.parser, 'aprocess') as mock_parse, \
             patch.object(document_processor, '_generate_embeddings', 
                         return_value=[[0.1] * 1536]):
            
            # Setup mock parser response
            mock_parse.return_value.get_markdown.return_value = content
            
            result = await document_processor.process_document(str(path))
            
            assert result['family'] == 'eco'
            assert 'Change Details' in result['content']['sections']
            assert 'CMP-2002' in result['content']['entities'].get('component', [])
            
    finally:
        path.unlink()