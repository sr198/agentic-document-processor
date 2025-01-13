# examples/impact_analysis_scenarios.py

import asyncio
from api_client import ImpactAnalysisClient, QueryType
from pathlib import Path
import json
from typing import Dict, Any

async def run_component_impact_scenario(client: ImpactAnalysisClient):
    """Scenario 1: Analyzing component changes"""
    print("\n=== Component Impact Analysis Scenario ===")
    
    # 1. Check current usage
    result = await client.analyze_impact(
        query="Which devices and processes currently use CMP-2002 (Adhesive Strip)?",
        query_type=QueryType.COMPONENT_USAGE
    )
    print("\nCurrent Usage Analysis:")
    print(json.dumps(result, indent=2))
    
    # 2. Analyze process impacts
    result = await client.analyze_impact(
        query="What manufacturing processes would be affected by changing CMP-2002?",
        query_type=QueryType.PROCESS_IMPACT
    )
    print("\nProcess Impact Analysis:")
    print(json.dumps(result, indent=2))
    
    # 3. Check regulatory implications
    result = await client.analyze_impact(
        query="What regulatory submissions or requirements are tied to CMP-2002?",
        query_type=QueryType.REGULATORY_IMPACT
    )
    print("\nRegulatory Impact Analysis:")
    print(json.dumps(result, indent=2))

async def run_process_change_scenario(client: ImpactAnalysisClient):
    """Scenario 2: Analyzing process changes"""
    print("\n=== Process Change Analysis Scenario ===")
    
    # 1. Analyze process dependencies
    result = await client.analyze_impact(
        query="What components and devices depend on Assembly Line #2?",
        query_type=QueryType.PROCESS_IMPACT
    )
    print("\nProcess Dependencies:")
    print(json.dumps(result, indent=2))
    
    # 2. Check quality implications
    result = await client.analyze_impact(
        query="What quality metrics and validation requirements are associated with Assembly Line #2?",
        query_type=QueryType.PROCESS_IMPACT
    )
    print("\nQuality Implications:")
    print(json.dumps(result, indent=2))

async def run_regulatory_impact_scenario(client: ImpactAnalysisClient):
    """Scenario 3: Analyzing regulatory impacts"""
    print("\n=== Regulatory Impact Analysis Scenario ===")
    
    # 1. Check submission dependencies
    result = await client.analyze_impact(
        query="Which components and processes are affected by FDA submission 2023-K0123?",
        query_type=QueryType.REGULATORY_IMPACT
    )
    print("\nSubmission Dependencies:")
    print(json.dumps(result, indent=2))
    
    # 2. Analyze change requirements
    result = await client.analyze_impact(
        query="What regulatory requirements need to be met for changing components in FDA submission 2023-K0123?",
        query_type=QueryType.REGULATORY_IMPACT
    )
    print("\nChange Requirements:")
    print(json.dumps(result, indent=2))

async def run_timeline_analysis_scenario(client: ImpactAnalysisClient):
    """Scenario 4: Timeline analysis"""
    print("\n=== Timeline Analysis Scenario ===")
    
    result = await client.analyze_impact(
        query="What's the estimated timeline for implementing changes to CMP-2002, including regulatory approvals?",
        query_type=QueryType.TIMELINE
    )
    print("\nTimeline Analysis:")
    print(json.dumps(result, indent=2))

async def run_document_processing_scenario(client: ImpactAnalysisClient):
    """Scenario 5: Document processing workflow"""
    print("\n=== Document Processing Scenario ===")
    
    # Define test documents
    documents = [
        ("data/bom_updated.csv", "bom"),
        ("data/eco_2025_001.pdf", "eco"),
        ("data/process_validation_report.pdf", "process_validation"),
        ("data/regulatory_submission.pdf", "regulatory")
    ]
    
    for file_path, doc_type in documents:
        path = Path(file_path)
        if path.exists():
            print(f"\nProcessing {path.name}...")
            
            # Upload document
            upload_result = await client.upload_document(
                file_path=path,
                document_type=doc_type
            )
            print("Upload Result:", json.dumps(upload_result, indent=2))
            
            # Wait for processing
            try:
                process_result = await client.wait_for_document_processing(
                    upload_result["document_id"]
                )
                print("Processing Result:", json.dumps(process_result, indent=2))
            except Exception as e:
                print(f"Processing Error: {str(e)}")

async def main():
    # Initialize client
    async with ImpactAnalysisClient(
        base_url="http://localhost:8000",
        api_key="your-api-key"  # Optional
    ) as client:
        # Run scenarios
        await run_component_impact_scenario(client)
        await run_process_change_scenario(client)
        await run_regulatory_impact_scenario(client)
        await run_timeline_analysis_scenario(client)
        await run_document_processing_scenario(client)

if __name__ == "__main__":
    asyncio.run(main())