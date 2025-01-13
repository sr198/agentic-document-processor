# tools/load_documents.py

import asyncio
from pathlib import Path
from typing import List, Dict, Any
import yaml
import json
from api_client import ImpactAnalysisClient

class DocumentLoader:
    def __init__(self, base_url: str, data_dir: Path):
        self.client = ImpactAnalysisClient(base_url=base_url)
        self.data_dir = data_dir

    async def load_documents(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load all documents from data directory"""
        results = {
            "bom": [],
            "eco": [],
            "process_validation": [],
            "regulatory": []
        }
        
        # Document type patterns
        patterns = {
            "bom": ["*_BOM*.csv", "*BillOfMaterials*.csv"],
            "eco": ["*_ECO*.docx", "*_ChangeOrder*.pdf"],
            "process_validation": ["*_Process*.pdf", "*_Validation*.pdf"],
            "regulatory": ["*_FDA*.pdf", "*_Submission*.pdf"]
        }
        
        async with self.client:
            for doc_type, file_patterns in patterns.items():
                for pattern in file_patterns:
                    for file_path in self.data_dir.glob(pattern):
                        try:
                            print(f"Processing {file_path}...")
                            
                            # Upload document
                            upload_result = await self.client.upload_document(
                                file_path=file_path,
                                document_type=doc_type
                            )
                            
                            # Wait for processing to complete
                            process_result = await self.client.wait_for_document_processing(
                                upload_result["document_id"]
                            )
                            
                            results[doc_type].append({
                                "file": str(file_path),
                                "upload_result": upload_result,
                                "process_result": process_result
                            })
                            
                            print(f"Successfully processed {file_path}")
                            
                        except Exception as e:
                            print(f"Error processing {file_path}: {str(e)}")
                            results[doc_type].append({
                                "file": str(file_path),
                                "error": str(e)
                            })
        
        return results

    def save_results(self, results: Dict[str, List[Dict[str, Any]]], output_file: Path):
        """Save processing results to file"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)

async def main():
    # Configure data directory
    data_dir = Path("data")
    output_file = data_dir / "processing_results.json"
    
    # Initialize loader
    loader = DocumentLoader(
        base_url="http://localhost:8000",
        data_dir=data_dir
    )
    
    # Load documents
    print("Starting document loading process...")
    results = await loader.load_documents()
    
    # Save results
    loader.save_results(results, output_file)
    print(f"\nResults saved to {output_file}")
    
    # Print summary
    print("\nProcessing Summary:")
    for doc_type, docs in results.items():
        successful = len([d for d in docs if "error" not in d])
        total = len(docs)
        print(f"{doc_type}: {successful}/{total} documents processed successfully")

if __name__ == "__main__":
    asyncio.run(main())