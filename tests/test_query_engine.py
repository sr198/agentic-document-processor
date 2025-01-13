# tests/test_query_engine.py

import pytest
from app.core.query_engine import ImpactQueryEngine, QueryType
from app.core.graph_manager import GraphManager

@pytest.fixture
def query_engine():
    graph_manager = GraphManager()
    engine = ImpactQueryEngine(graph_manager)
    yield engine
    graph_manager.close()

@pytest.mark.asyncio
async def test_query_classification():
    """Test query classification"""
    engine = query_engine()
    
    # Test component usage query
    query_type = await engine._classify_query(
        "Which devices use component CMP-2002?"
    )
    assert query_type == QueryType.COMPONENT_USAGE
    
    # Test process impact query
    query_type = await engine._classify_query(
        "What manufacturing processes will be affected by changing CMP-2002?"
    )
    assert query_type == QueryType.PROCESS_IMPACT
    
    # Test full impact query
    query_type = await engine._classify_query(
        "What would be the total impact of replacing CMP-2002 with a new version?"
    )
    assert query_type == QueryType.FULL_IMPACT

@pytest.mark.asyncio
async def test_entity_extraction():
    """Test entity extraction from queries"""
    engine = query_engine()
    
    entities = await engine._extract_entities(
        "What's the impact of changing CMP-2002 on Assembly Line #2?"
    )
    
    assert 'CMP-2002' in entities.get('component_ids', [])
    assert 'Assembly Line #2' in entities.get('process_ids', [])

@pytest.mark.asyncio
async def test_component_usage_query():
    """Test component usage query handling"""
    engine = query_engine()
    
    result = await engine.execute_query(
        "Which devices use CMP-2002?",
        QueryType.COMPONENT_USAGE
    )
    
    assert result['query_type'] == 'component_usage'
    assert 'CMP-2002' in result['results']
    assert 'direct_impacts' in result['results']['CMP-2002']

@pytest.mark.asyncio
async def test_full_impact_query():
    """Test full impact analysis"""
    engine = query_engine()
    
    result = await engine.execute_query(
        "What would be the total impact of replacing CMP-2002?",
        QueryType.FULL_IMPACT
    )
    
    assert result['query_type'] == 'full_impact'
    assert 'component_impacts' in result
    assert 'process_impacts' in result
    assert 'regulatory_impacts' in result
    assert 'relevant_context' in result

@pytest.mark.asyncio
async def test_timeline_analysis():
    """Test timeline analysis query"""
    engine = query_engine()
    
    result = await engine.execute_query(
        "What's the timeline for implementing changes to CMP-2002?",
        QueryType.TIMELINE
    )
    
    assert result['query_type'] == 'timeline'
    assert 'results' in result
    assert any('component' in timeline for timeline in result['results'])