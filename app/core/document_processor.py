# app/core/document_processor.py

from pathlib import Path
from typing import Dict, List, Optional, Any
from llama_parse import LlamaParse
import openai
from loguru import logger
import pandas as pd
from datetime import datetime
import re
from .config import get_settings, get_document_config

class DocumentProcessor:
    """Processes documents and extracts structured information"""
    
    def __init__(self):
        self.settings = get_settings()
        self.config = get_document_config()
        
        # Initialize LlamaParse
        self.parser = LlamaParse(
            api_key=self.settings.LLAMAPARSE_API_KEY,
            result_type="markdown"
        )
        
        # Initialize OpenAI for embeddings
        openai.api_key = self.settings.OPENAI_API_KEY
    
    def identify_document_family(self, filename: str) -> Optional[str]:
        """Identify document family based on filename patterns"""
        for family, config in self.config["document_families"].items():
            patterns = config.get("patterns", [])
            for pattern in patterns:
                if re.match(pattern.replace("*", ".*"), filename):
                    return family
        return None

    async def process_document(self, file_path: str) -> Dict[str, Any]:
        """Process a document and extract structured content"""
        file_path = Path(file_path)
        family = self.identify_document_family(file_path.name)
        
        if not family:
            raise ValueError(f"Unable to identify document family for {file_path.name}")
        
        logger.info(f"Processing document {file_path.name} as {family}")
        
        # Parse document based on family type
        family_config = self.config["document_families"][family]
        if family_config["type"] == "structured":
            content = await self._process_structured_document(file_path, family_config)
        else:
            content = await self._process_unstructured_document(file_path, family_config)
        
        # Generate embeddings for text chunks
        embeddings = await self._generate_embeddings(content["text_chunks"])
        
        return {
            "family": family,
            "content": content,
            "embeddings": embeddings,
            "metadata": {
                "filename": file_path.name,
                "processed_at": datetime.utcnow().isoformat(),
                "processor_version": "1.0"
            }
        }

    async def _process_structured_document(
        self, file_path: Path, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process structured documents (e.g., CSV)"""
        df = pd.read_csv(file_path)
        
        # Extract relationships based on configuration
        relationships = []
        extract_settings = config.get("extract_settings", {})
        for rel_config in extract_settings.get("relationships", []):
            source_field = rel_config["source_field"]
            target_field = rel_config["target_field"]
            
            for _, row in df.iterrows():
                relationships.append({
                    "type": rel_config["type"],
                    "source": row[source_field],
                    "target": row[target_field]
                })
        
        # Create text chunks for embedding
        text_chunks = []
        for _, row in df.iterrows():
            chunk = " | ".join(f"{col}: {val}" for col, val in row.items())
            text_chunks.append(chunk)
        
        return {
            "structured_data": df.to_dict(orient="records"),
            "relationships": relationships,
            "text_chunks": text_chunks
        }

    async def _process_unstructured_document(
        self, file_path: Path, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process unstructured documents using LlamaParse"""
        # Parse document
        doc_content = await self.parser.aprocess(str(file_path))
        content = doc_content.get_markdown()
        
        # Extract sections based on configuration
        sections = {}
        parser_settings = config.get("parser_settings", {})
        for section_name in parser_settings.get("sections", []):
            section_content = self._extract_section(content, section_name)
            if section_content:
                sections[section_name] = section_content
        
        # Extract entities and relationships
        extract_settings = config.get("extract_settings", {})
        entities = self._extract_entities(content, extract_settings.get("entities", []))
        relationships = self._extract_relationships(
            content, extract_settings.get("relationships", [])
        )
        
        # Create text chunks
        text_chunks = self._create_text_chunks(content)
        
        return {
            "sections": sections,
            "entities": entities,
            "relationships": relationships,
            "text_chunks": text_chunks,
            "raw_content": content
        }

    def _extract_section(self, content: str, section_name: str) -> Optional[str]:
        """Extract content of a specific section"""
        pattern = f"#{{{1,6}}}\\s*{section_name}\\s*\n(.*?)(?=#{{{1,6}}}|$)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else None

    def _extract_entities(
        self, content: str, entity_configs: List[Dict[str, Any]]
    ) -> Dict[str, List[str]]:
        """Extract entities based on patterns"""
        entities = {}
        for entity_config in entity_configs:
            pattern = entity_config["pattern"]
            matches = re.findall(pattern, content)
            if matches:
                entities[entity_config["name"]] = matches
        return entities

    def _extract_relationships(
        self, content: str, relationship_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        """Extract relationships based on patterns"""
        relationships = []
        for rel_config in relationship_configs:
            source_matches = re.findall(rel_config["source_pattern"], content)
            target_matches = re.findall(rel_config["target_pattern"], content)
            
            for source in source_matches:
                for target in target_matches:
                    relationships.append({
                        "type": rel_config["type"],
                        "source": source,
                        "target": target
                    })
        return relationships

    def _create_text_chunks(
        self, content: str, chunk_size: int = 1000
    ) -> List[str]:
        """Split content into chunks for embedding"""
        chunks = []
        paragraphs = content.split("\n\n")
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = paragraph
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    async def _generate_embeddings(self, text_chunks: List[str]) -> List[List[float]]:
        """Generate embeddings for text chunks"""
        embeddings = []
        for chunk in text_chunks:
            try:
                response = await openai.Embedding.acreate(
                    input=chunk,
                    model="text-embedding-ada-002"
                )
                embeddings.append(response["data"][0]["embedding"])
            except Exception as e:
                logger.error(f"Error generating embedding: {str(e)}")
                embeddings.append([0.0] * 1536)  # Default empty embedding
        return embeddings