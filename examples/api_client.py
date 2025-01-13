# examples/api_client.py

import httpx
import asyncio
from typing import Dict, List, Optional, Any
from pathlib import Path
import json
from dataclasses import dataclass
from enum import Enum

class QueryType(str, Enum):
    COMPONENT_USAGE = "component_usage"
    PROCESS_IMPACT = "process_impact"
    REGULATORY_IMPACT = "regulatory_impact"
    FULL_IMPACT = "full_impact"
    TIMELINE = "timeline"
    CUSTOM = "custom"

@dataclass
class ImpactAnalysisClient:
    """Client for interacting with the Impact Analysis API"""
    base_url: str
    api_key: Optional[str] = None
    timeout: int = 30

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.api_key}" if self.api_key else None
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def analyze_impact(
        self, 
        query: str, 
        query_type: Optional[QueryType] = None,
        include_context: bool = True
    ) -> Dict[str, Any]:
        """Execute an impact analysis query"""
        payload = {
            "query": query,
            "query_type": query_type.value if query_type else None,
            "include_context": include_context
        }

        response = await self.client.post("/api/v1/impact-analysis", json=payload)
        response.raise_for_status()
        return response.json()

    async def upload_document(
        self, 
        file_path: Path, 
        document_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload a document for processing"""
        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            data = {"document_type": document_type} if document_type else {}
            
            response = await self.client.post(
                "/api/v1/documents/upload",
                files=files,
                data=data
            )
            response.raise_for_status()
            return response.json()

    async def get_document_status(self, document_id: str) -> Dict[str, Any]:
        """Check the status of a document processing job"""
        response = await self.client.get(f"/api/v1/documents/{document_id}")
        response.raise_for_status()
        return response.json()

    async def wait_for_document_processing(
        self, 
        document_id: str,
        check_interval: int = 5,
        max_attempts: int = 12
    ) -> Dict[str, Any]:
        """Wait for document processing to complete"""
        for _ in range(max_attempts):
            status = await self.get_document_status(document_id)
            if status["status"] == "completed":
                return status
            elif status["status"] == "error":
                raise Exception(f"Document processing failed: {status}")
            await asyncio.sleep(check_interval)
        
        raise TimeoutError("Document processing took too long")

# Example usage
async def main():
    # Initialize client
    async with ImpactAnalysisClient(
        base_url="http://localhost:8000",
        api_key="your-api-key"  # Optional
    ) as client:
        try:
            # Example 1: Component Usage Query
            result = await client.analyze_impact(
                query="Which devices use component CMP-2002?",
                query_type=QueryType.COMPONENT_USAGE
            )
            print("Component Usage Analysis:")
            print(json.dumps(result, indent=2))

            # Example 2: Full Impact Analysis
            result = await client.analyze_impact(
                query="What would be the total impact of replacing CMP-2002?",
                query_type=QueryType.FULL_IMPACT
            )
            print("\nFull Impact Analysis:")
            print(json.dumps(result, indent=2))

            # Example 3: Upload and Process BOM
            bom_path = Path("data/sample_bom.csv")
            if bom_path.exists():
                upload_result = await client.upload_document(
                    file_path=bom_path,
                    document_type="bom"
                )
                print("\nDocument Upload Result:")
                print(json.dumps(upload_result, indent=2))

                # Wait for processing to complete
                process_result = await client.wait_for_document_processing(
                    upload_result["document_id"]
                )
                print("\nProcessing Result:")
                print(json.dumps(process_result, indent=2))

        except httpx.HTTPStatusError as e:
            print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"Error: {str(e)}")

# Run examples
if __name__ == "__main__":
    asyncio.run(main())