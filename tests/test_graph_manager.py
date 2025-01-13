# tests/test_graph_manager.py

import pytest
from app.core.graph_manager import GraphManager
import numpy as np
from datetime import datetime

@pytest.fixture
def graph_manager():
    manager = GraphManager()
    yield manager
    manager.close()

@pytest.fixture
def sample_bom_data():
    return {
        'family': 'bom',
        'content': {
            'structured_data': [
                {
                    'component_id': 'CMP-2002',
                    'component_name': 'Adhesive Strip',
                    'device_name': 'GlucoMonitor Pro 2000',
                    'version': 'v1.2',
                    'supplier_name': 'AdheSeal Inc'
                }
            ],
            'text_chunks': ['Sample BOM text chunk'],
            'relationships': [
                {
                    'type': 'USED_IN',
                    'source': 'CMP-2002',
                    'target': 'GlucoMonitor Pro 2000'
                }
            ]
        },
        'embeddings': [np.random.rand(1536).tolist()],
        'metadata': {
            'filename': 'test_bom.csv',
            'processed_at': str(datetime.now())
        }
    }

@pytest.mark.asyncio
async def test_store_bom_document(graph_manager, sample_bom_data):
    await graph_manager.store_processed_document(sample_bom_data)
    
    # Verify component was stored
    result = await graph_manager.find_component_impacts('CMP-2002')
    assert result['component']['name'] == 'Adhesive Strip'
    assert len(result['devices']) == 1
    assert result['devices'][0]['name'] == 'GlucoMonitor Pro 2000'

@pytest.mark.asyncio
async def test_find_similar_chunks(graph_manager, sample_bom_data):
    # Store sample data
    await graph_manager.store_processed_document(sample_bom_data)
    
    # Test similarity search
    query_embedding = np.random.rand(1536).tolist()
    results = await graph_manager.find_similar_chunks(query_embedding, limit=1)
    
    assert len(results) == 1
    assert results[0]['family'] == 'bom'
    assert results[0]['filename'] == 'test_bom.csv'

@pytest.fixture
def sample_eco_data():
    return {
        'family': 'eco',
        'content': {
            'sections': {
                'Change Details': 'Change to adhesive formula'
            },
            'entities': {
                'eco_number': ['ECO-2025-001'],
                'component': ['CMP-2002']
            },
            'text_chunks': ['Sample ECO text chunk']
        },
        'embeddings': [np.random.rand(1536).tolist()],
        'metadata': {
            'filename': 'test_eco.pdf',
            'processed_at': str(datetime.now())
        }
    }

@pytest.mark.asyncio
async def test_component_impact_analysis(graph_manager, sample_bom_data, sample_eco_data):
    # Store both BOM and ECO data
    await graph_manager.store_processed_document(sample_bom_data)
    await graph_manager.store_processed_document(sample_eco_data)
    
    # Verify impact analysis
    result = await graph_manager.find_component_impacts('CMP-2002')
    assert len(result['devices']) == 1
    assert len(result['changes']) == 1
    assert result['changes'][0]['id'] == 'ECO-2025-001'