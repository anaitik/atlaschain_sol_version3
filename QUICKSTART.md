# AtlasChain Quick Start Guide

## Architecture Verification

The system matches the architecture diagram with:

### Reasoning Plane (AI Agents) ✓
- ✅ **Schema Inference Agent** (`agents/schema_agent.py`)
- ✅ **Normalization & Assumptions Agent** (`agents/normalization_agent.py`)
- ✅ **Metric Intent Agent** (`agents/metric_intent_agent.py`)
- ✅ **Code Generation Agent** (`agents/codegen_agent.py`)

### Tool Plane ✓
- ✅ **Data Inspection Tools** (`backend/tools/data_inspection.py`)
- ✅ **Reference Tools** (`backend/tools/reference_tools.py`)
- ✅ **Simulation Tools** (`backend/tools/simulation_tools.py`)
- ✅ **Execution Tools** (`backend/tools/execution_tools.py`)

### Pipeline Plane ✓
- ✅ **Pipeline Runner** (`backend/services/pipeline_service.py`)
- ✅ **Evidence Bundles** (stored in `storage/evidence/`)
- ✅ **Blockchain Anchoring** (`backend/blockchain.py` - Algorand)
- ✅ **Report Generation** (XHTML-based ESG reports)

## Quick Start

### 1. Backend Setup

```bash
# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Prepare environment variables (copy example and edit values)
# Windows (PowerShell):
Copy-Item .env.example .env
# Linux/Mac:
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run backend
cd backend
python main.py
```

Backend will run on http://localhost:8000

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on http://localhost:3000

### 3. Create Your First Pipeline

1. Go to http://localhost:3000
2. Click "Create New Pipeline"
3. Upload a sample CSV file
4. Enter pipeline name and description
5. Select ESG standard (optional)
6. Click "Create Pipeline"

The system will:
- Analyze your data schema
- Identify normalization needs
- Propose ESG metrics
- Generate transformation code

### 4. Execute Pipeline

1. Go to "Pipelines" page
2. Click "Execute" on a pipeline
3. Upload a batch CSV file
4. Click "Execute Pipeline"

The system will:
- Transform the data
- Calculate metrics
- Generate ESG report
- Create evidence bundle
- Anchor to blockchain (if enabled)

## Configuration

### ESG Standards

Navigate to "ESG Standards" to:
- View default standards (GRI, CSRD, SEC)
- Create custom standards
- Configure metrics per region/framework

### Blockchain (Algorand)

For production use:
1. Set up Algorand account
2. Update `backend/blockchain.py`:
   - Set `algod_address` to mainnet
   - Configure `algod_token`
   - Use real account credentials

For development, mock anchors are used.

## Data Flow

1. **Upload** → File saved to `storage/uploads/`
2. **Bronze** → Raw data copied to `storage/bronze/`
3. **Silver** → Transformed data saved to `storage/silver/`
4. **Gold** → Final output saved to `storage/gold/`
5. **Evidence** → Bundle saved to `storage/evidence/`
6. **Anchor** → Metadata saved to `storage/anchors/`

## API Endpoints

- `GET /api/pipelines` - List all pipelines
- `POST /api/pipelines/create-from-file` - Create pipeline
- `POST /api/pipelines/execute` - Execute pipeline
- `GET /api/esg-standards` - List ESG standards
- `POST /api/upload` - Upload CSV file

Full API docs: http://localhost:8000/docs

## Troubleshooting

### Backend won't start
- Check Python version (3.8+)
- Verify all dependencies installed
- Check port 8000 is available

### Frontend won't start
- Run `npm install` in frontend directory
- Check Node.js version (16+)
- Verify port 3000 is available

### Pipeline creation fails
- Check CSV file format
- Verify LLM API key is set
- Check backend logs for errors

### Execution fails
- Verify input CSV matches pipeline schema
- Check transform code for errors
- Review execution logs

## Next Steps

- Configure ESG standards for your region
- Set up Algorand for production anchoring
- Customize report templates
- Add custom reference data

