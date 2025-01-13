# tests/conftest.py

import pytest
from dotenv import load_dotenv
from pathlib import Path
import os

# Load environment variables and print for debugging
def print_env_vars():
    load_dotenv()
    print("\nLoaded Environment Variables:")
    required_vars = [
        'OPENAI_API_KEY',
        'NEO4J_PASSWORD',
        'LLAMAPARSE_API_KEY',
        'API_V1_STR',
        'PROJECT_NAME',
        'NEO4J_URI',
        'NEO4J_USER',
        'LOG_LEVEL'
    ]
    for var in required_vars:
        print(f"{var}: {os.environ.get(var, 'NOT SET')}")

print_env_vars()

@pytest.fixture(scope="session")
def mock_settings():
    """Mock settings for testing"""
    from app.core.config import Settings
    return Settings(
        OPENAI_API_KEY="test-key",
        NEO4J_PASSWORD="test-password",
        LLAMAPARSE_API_KEY="test-key",
        API_V1_STR="/api/v1",
        PROJECT_NAME="Impact Analysis API",
        NEO4J_URI="bolt://neo4j:7687",
        NEO4J_USER="neo4j",
        LOG_LEVEL="INFO"
    )

# This will be used instead of real settings in tests
@pytest.fixture(autouse=True)
def patch_settings(monkeypatch, mock_settings):
    """Automatically patch settings for all tests"""
    from app.core.config import get_settings
    monkeypatch.setattr("app.core.config.get_settings", lambda: mock_settings)

@pytest.fixture(scope="session")
def document_processor(mock_settings):
    """Provides document processor instance with mock settings"""
    from app.core.document_processor import DocumentProcessor
    return DocumentProcessor()

@pytest.fixture(scope="session")
def graph_manager(mock_settings):
    """Provides graph manager instance with mock settings"""
    from app.core.graph_manager import GraphManager
    manager = GraphManager()
    yield manager
    manager.close()

@pytest.fixture
def sample_data_dir():
    """Provides path to sample data directory"""
    return Path("tests/sample_data")

# Ensure test directories exist
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment(tmp_path_factory):
    """Setup necessary directories and files for testing"""
    # Create test directories if they don't exist
    test_data_dir = Path("tests/sample_data")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Create config directory if it doesn't exist
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)