# Impact Analysis API

A system for analyzing impacts of changes in medical device manufacturing using document processing and graph-based analysis.

## Setup

1. **Environment Setup**
```bash
# Clone repository
git clone <repository-url>
cd impact-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your configuration
```

2. **Docker Setup**
```bash
# Start services
docker-compose up -d

# Check services
docker-compose ps
```

## Loading Documents

Use the document loader tool:
```bash
python tools/load_documents.py
```

Place your documents in the following structure:
```
data/
├── bom/          # Bill of Materials
├── eco/          # Engineering Change Orders
├── process/      # Process Validation Reports
└── regulatory/   # Regulatory Submissions
```

## API Usage

1. **Document Upload**
```python
from examples.api_client import ImpactAnalysisClient

async with ImpactAnalysisClient("http://localhost:8000") as client:
    result = await client.upload_document(
        file_path="data/bom/BOM_MedicalDevice_XYZ.csv",
        document_type="bom"
    )
```

2. **Impact Analysis**
```python
result = await client.analyze_impact(
    query="What would be the total impact of replacing CMP-2002?",
    query_type="full_impact"
)
```

## Development

1. **Running Tests**
```bash
pytest
```

2. **Code Style**
```bash
# Install development dependencies
pip install black isort flake8

# Format code
black .
isort .

# Check style
flake8
```

## Project Structure

- `app/`: Main application code
  - `api/`: FastAPI application and routes
  - `core/`: Core business logic
  - `schemas/`: Shared data models
  - `utils/`: Utility functions
- `config/`: Configuration files
- `examples/`: Example usage code
- `tools/`: Utility scripts
- `tests/`: Test suite

## Configuration

1. **Environment Variables**
See `.env.example` for required configuration.

2. **Document Processing**
Edit `config/document_families.yaml` for document type definitions.

3. **Relationship Rules**
Edit `config/relationship_rules.yaml` for relationship extraction rules.