# app/core/config.py

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache
import yaml
from pathlib import Path
from typing import Dict, Any

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    # API Settings
    API_V1_STR: str = Field(default="/api/v1")
    PROJECT_NAME: str = Field(default="Impact Analysis API")
    
    # OpenAI Settings
    OPENAI_API_KEY: str = Field(default="test-key")
    
    # Neo4j Settings
    NEO4J_URI: str = Field(default="bolt://neo4j:7687")
    NEO4J_USER: str = Field(default="neo4j")
    NEO4J_PASSWORD: str = Field(default="test-password")
    
    # Document Processing
    LLAMAPARSE_API_KEY: str = Field(default="test-key")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

def load_yaml_config(path: Path) -> Dict[str, Any]:
    """Load YAML configuration file"""
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    
    with open(path) as f:
        return yaml.safe_load(f)

def get_document_config() -> Dict[str, Any]:
    """Get document processing configuration"""
    config_dir = Path("config")
    return {
        "document_families": load_yaml_config(config_dir / "document_families.yaml"),
        "relationship_rules": load_yaml_config(config_dir / "relationship_rules.yaml")
    }