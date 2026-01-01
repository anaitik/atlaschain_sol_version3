# AtlasChain - Agentic ESG Audit Preparation Platform

A production-grade platform for preparing ESG audit data using AI agents, with blockchain anchoring and configurable ESG standards.

## Architecture

The platform follows a multi-layered architecture:

### Reasoning Plane (AI Agents)
- **Schema Inference Agent**: Infers semantic meaning from data columns
- **Normalization & Assumptions Agent**: Identifies missing fields, data quality issues, and proposes assumptions
- **Metric Intent Agent**: Designs ESG risk metrics based on schema
- **Code Generation Agent**: Generates transformation code and ESG reports

### Tool Plane
- **Data Inspection Tools**: Get headers, sample rows, column statistics
- **Reference Tools**: Lookup emissions, materials, transport distances
- **Simulation Tools**: Simulate assumptions, preview metric impacts
- **Execution Tools**: Sandboxed code runner

### Pipeline Plane
- Pipeline execution engine
- Evidence bundle generation
- Blockchain anchoring (Algorand)
- Report generation

## Features

- **Pipeline Management**: Create, save, and execute pipelines on batches of data
- **ESG Standards Configuration**: Configurable standards per region/framework (GRI, CSRD, SEC, etc.)
- **Blockchain Anchoring**: Immutable audit trail using Algorand
- **Evidence Bundles**: Complete audit trail with schema, assumptions, metrics, and code
- **ESG Reports**: Standards-based XHTML reports ready for submission

## Setup

### Backend

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` from `.env.example` and set environment variables (recommended):
```bash
# copy example
cp .env.example .env
# Edit .env and add your secrets, e.g.:
# GOOGLE_API_KEY="your-api-key"  # For LLM
# ALGOD_TOKEN="your-algod-token"  # For Algorand (optional)
```

4. Run backend:
```bash
cd backend
python main.py
# Or: uvicorn main:app --reload
```

Backend runs on http://localhost:8000

### Frontend

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Run development server:
```bash
npm run dev
```

Frontend runs on http://localhost:3000

## Usage

### Creating a Pipeline

1. Upload a sample CSV file with your ESG data
2. The system will:
   - Infer the schema
   - Identify normalization needs
   - Propose ESG metrics
   - Generate transformation code
3. Review and save the pipeline

### Executing a Pipeline

1. Select a saved pipeline
2. Upload a batch CSV file
3. The system will:
   - Transform the data
   - Calculate metrics
   - Generate ESG report
   - Create evidence bundle
   - Anchor to blockchain (optional)

### ESG Standards Configuration

1. Navigate to ESG Standards page
2. Create or edit standards for your region/framework
3. Configure required metrics, reporting frequency, etc.
4. Assign standards to pipelines

## Database

SQLite database (`atlaschain.db`) stores:
- Pipelines
- ESG Standards
- Pipeline Executions
- Blockchain Anchors

## Storage

Local file storage structure:
- `storage/bronze/`: Raw input data
- `storage/silver/`: Transformed data
- `storage/gold/`: Final output data
- `storage/evidence/`: Evidence bundles
- `storage/anchors/`: Anchor metadata

## Blockchain Integration

The platform uses Algorand for blockchain anchoring. For production:
1. Set up Algorand account
2. Configure `ALGOD_TOKEN` and `ALGOD_ADDRESS`
3. Update `backend/blockchain.py` with production credentials

For development, the system uses mock anchors.

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## License

Proprietary - All rights reserved

