"""
FastAPI main application for AtlasChain backend.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path to import agents and llm modules
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))

# Load environment variables from .env
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import sqlite3

from database import Database
from storage import StorageManager
from blockchain import AlgorandAnchor
from services.pipeline_service import PipelineService
from services.esg_service import ESGService
from services.report_service import ReportService
from tools.data_inspection import DataInspectionTools
from auth import AuthService
from middleware import get_current_user, get_current_admin_user, security
from fastapi.security import HTTPAuthorizationCredentials
from fastapi import Depends

# Initialize components
db = Database()
storage = StorageManager()

# Initialize blockchain with credentials from environment or defaults
try:
    blockchain = AlgorandAnchor(
        algod_address=os.getenv("ALGONODE_URL", "https://testnet-api.algonode.cloud"),
        sender_address=os.getenv("ALGORAND_ADDRESS"),
        sender_mnemonic=os.getenv("ALGORAND_MNEMONIC")
    )
    print("Blockchain initialized successfully")
except Exception as e:
    print(f"Warning: Failed to initialize blockchain: {e}")
    # Fallback: will fail when trying to anchor
    blockchain = None

auth_service = AuthService(db)
pipeline_service = PipelineService(db, storage, blockchain)
esg_service = ESGService(db)
report_service = ReportService(db)

# Initialize default ESG standards
def init_default_standards():
    """Initialize default ESG standards if they don't exist."""
    existing = esg_service.list_standards()
    if not existing:
        defaults = esg_service.get_default_standards()
        for std in defaults:
            esg_service.create_standard(
                name=std["name"],
                config=std["config"],
                region=std["region"],
                framework=std["framework"],
                description=std["description"]
            )

init_default_standards()

# FastAPI app
app = FastAPI(
    title="AtlasChain API",
    description="Agentic ESG Audit Preparation Platform",
    version="1.0.0"
)

# CORS middleware - allow frontend domain + localhost for dev
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://atlaschain-frontend-production.up.railway.app")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PipelineCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    esg_standard_id: Optional[int] = None
    created_by: str = "system"

class PipelineExecuteRequest(BaseModel):
    pipeline_id: int
    input_file_path: str
    anchor_to_blockchain: bool = True
    executed_by: str = "system"

class ESGStandardCreateRequest(BaseModel):
    name: str
    config: Dict[str, Any]
    region: str = ""
    framework: str = ""
    description: str = ""

class UserRegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = ""

class UserLoginRequest(BaseModel):
    username: str
    password: str

# Routes
@app.get("/")
async def root():
    return {"message": "AtlasChain API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Authentication routes (public)
@app.post("/api/auth/register")
async def register_user(request: UserRegisterRequest):
    """Register a new user (pending admin approval)."""
    try:
        result = auth_service.register_user(
            username=request.username,
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/api/auth/login")
async def login_user(request: UserLoginRequest):
    """Login user and get access token."""
    user = auth_service.authenticate_user(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password, or account not approved"
        )
    
    access_token = auth_service.create_access_token(user)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user.get("full_name", "")
        }
    }

@app.get("/api/auth/me")
async def get_current_user_info(
    current_user: dict = Depends(get_current_user)
):
    """Get current user information."""
    user = auth_service.get_user(current_user["id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Admin routes
@app.get("/api/admin/registrations")
async def get_pending_registrations(
    current_user: dict = Depends(get_current_admin_user)
):
    """Get all pending user registrations (admin only)."""
    registrations = auth_service.get_pending_registrations()
    return {"registrations": registrations}

@app.post("/api/admin/registrations/{registration_id}/approve")
async def approve_registration(
    registration_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """Approve a user registration (admin only)."""
    try:
        result = auth_service.approve_user(registration_id, current_user["id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/admin/registrations/{registration_id}/reject")
async def reject_registration(
    registration_id: int,
    current_user: dict = Depends(get_current_admin_user)
):
    """Reject a user registration (admin only)."""
    try:
        result = auth_service.reject_user(registration_id, current_user["id"])
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/admin/users")
async def list_all_users(
    current_user: dict = Depends(get_current_admin_user)
):
    """List all users (admin only)."""
    conn = db.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, username, email, role, is_approved, is_active, full_name, created_at
        FROM users
        ORDER BY created_at DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return {"users": [dict(row) for row in rows]}

# File upload (protected)
@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a CSV file for pipeline creation."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    content = await file.read()
    file_path = storage.save_upload(content, file.filename)
    
    return {
        "file_path": file_path,
        "filename": file.filename,
        "size": len(content)
    }

# Data inspection (protected)
@app.get("/api/inspect/{file_path:path}")
async def inspect_file(
    file_path: str,
    current_user: dict = Depends(get_current_user)
):
    """Inspect uploaded file."""
    try:
        headers = DataInspectionTools.get_headers(file_path)
        samples = DataInspectionTools.get_sample_rows(file_path)
        stats = DataInspectionTools.get_column_stats(file_path)
        
        return {
            "headers": headers,
            "samples": samples,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Pipeline management (protected)
@app.post("/api/pipelines/create-from-file")
async def create_pipeline_from_file(
    file_path: str,
    pipeline_name: str,
    description: str = "",
    esg_standard_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """Create pipeline from file path."""
    try:
        import traceback
        result = await pipeline_service.create_pipeline_from_sample(
            csv_path=file_path,
            pipeline_name=pipeline_name,
            description=description,
            esg_standard_id=esg_standard_id,
            created_by=current_user["username"]
        )
        return result
    except Exception as e:
        import traceback
        error_detail = str(e)
        error_traceback = traceback.format_exc()
        print(f"Error creating pipeline: {error_detail}")
        print(f"Traceback: {error_traceback}")
        raise HTTPException(status_code=500, detail=f"{error_detail}\n\nTraceback:\n{error_traceback}")

@app.get("/api/pipelines")
async def list_pipelines(current_user: dict = Depends(get_current_user)):
    """List pipelines. Users see only their own, admins see all."""
    pipelines = db.list_pipelines(
        created_by=current_user["username"] if current_user.get("role") != "admin" else None,
        user_role=current_user.get("role")
    )
    return {"pipelines": pipelines}

@app.get("/api/pipelines/{pipeline_id}")
async def get_pipeline(
    pipeline_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get pipeline details. Users can only access their own pipelines, admins can access all."""
    pipeline = db.get_pipeline(pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check access: users can only see their own pipelines, admins can see all
    if current_user.get("role") != "admin" and pipeline.get("created_by") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied: You can only view your own pipelines")
    
    # Parse JSON fields
    import json
    pipeline["schema_json"] = json.loads(pipeline["schema_json"])
    pipeline["normalization_json"] = json.loads(pipeline["normalization_json"])
    pipeline["metric_intent_json"] = json.loads(pipeline["metric_intent_json"])
    
    return pipeline

@app.post("/api/pipelines/execute")
async def execute_pipeline(
    request: PipelineExecuteRequest,
    current_user: dict = Depends(get_current_user)
):
    """Execute a pipeline."""
    try:
        result = await pipeline_service.execute_pipeline(
            pipeline_id=request.pipeline_id,
            input_csv_path=request.input_file_path,
            executed_by=current_user["username"],
            anchor_to_blockchain=request.anchor_to_blockchain
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ESG Standards (protected)
@app.get("/api/esg-standards")
async def list_esg_standards(current_user: dict = Depends(get_current_user)):
    """List all ESG standards."""
    standards = esg_service.list_standards()
    return {"standards": standards}

@app.get("/api/esg-standards/{standard_id}")
async def get_esg_standard(
    standard_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get ESG standard."""
    standard = esg_service.get_standard(standard_id)
    if not standard:
        raise HTTPException(status_code=404, detail="Standard not found")
    return standard

@app.post("/api/esg-standards")
async def create_esg_standard(
    request: ESGStandardCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create new ESG standard."""
    standard_id = esg_service.create_standard(
        name=request.name,
        config=request.config,
        region=request.region,
        framework=request.framework,
        description=request.description
    )
    return {"standard_id": standard_id, "status": "created"}

# Executions (protected)
@app.get("/api/executions")
async def list_executions(
    pipeline_id: Optional[int] = None,
    current_user: dict = Depends(get_current_user)
):
    """List pipeline executions. Users see only their own, admins see all."""
    executions = db.list_executions(
        pipeline_id=pipeline_id,
        executed_by=current_user["username"] if current_user.get("role") != "admin" else None,
        user_role=current_user.get("role")
    )
    
    # Enrich with pipeline names
    conn = db.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    enriched = []
    for exec in executions:
        # Check if user has access to the pipeline
        cursor.execute("SELECT name, created_by FROM pipelines WHERE id = ?", (exec["pipeline_id"],))
        pipeline_row = cursor.fetchone()
        if pipeline_row:
            # If not admin, verify user owns the pipeline
            if current_user.get("role") != "admin" and pipeline_row["created_by"] != current_user["username"]:
                continue  # Skip this execution
            exec["pipeline_name"] = pipeline_row["name"]
        else:
            exec["pipeline_name"] = "Unknown"
        enriched.append(exec)
    
    conn.close()
    return {"executions": enriched}

@app.get("/api/executions/{execution_id}")
async def get_execution(
    execution_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get execution details. Users can only access their own executions, admins can access all."""
    execution = db.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Check access: users can only see their own executions, admins can see all
    if current_user.get("role") != "admin" and execution.get("executed_by") != current_user["username"]:
        raise HTTPException(status_code=403, detail="Access denied: You can only view your own executions")
    
    # Enrich with pipeline info
    pipeline = db.get_pipeline(execution["pipeline_id"])
    if pipeline:
        # Also check pipeline access
        if current_user.get("role") != "admin" and pipeline.get("created_by") != current_user["username"]:
            raise HTTPException(status_code=403, detail="Access denied: You don't have access to this pipeline")
        execution["pipeline_name"] = pipeline["name"]
        execution["pipeline_description"] = pipeline.get("description", "")
    
    return execution

# Dashboard stats (protected)
@app.get("/api/dashboard/stats")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    """Get dashboard statistics. Users see only their own data, admins see all."""
    is_admin = current_user.get("role") == "admin"
    username = current_user["username"]
    
    # Get pipelines (filtered by user)
    pipelines = db.list_pipelines(
        created_by=username if not is_admin else None,
        user_role=current_user.get("role")
    )
    
    # Get executions (filtered by user)
    conn = db.get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    if is_admin:
        cursor.execute("SELECT * FROM pipeline_executions")
        executions = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT e.*, p.name as pipeline_name 
            FROM pipeline_executions e
            LEFT JOIN pipelines p ON e.pipeline_id = p.id
            ORDER BY e.started_at DESC 
            LIMIT 10
        """)
    else:
        cursor.execute("SELECT * FROM pipeline_executions WHERE executed_by = ?", (username,))
        executions = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT e.*, p.name as pipeline_name 
            FROM pipeline_executions e
            LEFT JOIN pipelines p ON e.pipeline_id = p.id
            WHERE e.executed_by = ?
            ORDER BY e.started_at DESC 
            LIMIT 10
        """, (username,))
    
    recent_executions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Calculate stats
    completed = sum(1 for e in executions if e.get("status") == "completed")
    failed = sum(1 for e in executions if e.get("status") == "failed")
    running = sum(1 for e in executions if e.get("status") == "running")
    
    return {
        "pipelines": len(pipelines),
        "executions": len(executions),
        "completed": completed,
        "failed": failed,
        "running": running,
        "recent_executions": recent_executions
    }

# Data preview (protected)
@app.get("/api/executions/{execution_id}/preview")
async def preview_execution_data(
    execution_id: int,
    limit: int = 10,
    current_user: dict = Depends(get_current_user)
):
    """Preview transformed data from execution."""
    execution = db.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    output_path = execution.get("output_file_path")
    if not output_path:
        raise HTTPException(status_code=404, detail="No output data available")

    try:
        import pandas as pd
        df = pd.read_csv(output_path, nrows=limit)

        # Handle NaN values to make JSON serializable
        df = df.fillna('')  # Replace NaN with empty string

        return {
            "columns": list(df.columns),
            "rows": df.to_dict(orient="records"),
            "row_count": len(df),
            "total_columns": len(df.columns)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading data: {str(e)}")

# Report endpoints (protected)
@app.get("/api/executions/{execution_id}/report")
async def get_execution_report(
    execution_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get ESG report for execution."""
    execution = db.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    # Try to get report from metrics_json first
    metrics_json = execution.get("metrics_json")
    if metrics_json:
        import json
        metrics = json.loads(metrics_json) if isinstance(metrics_json, str) else metrics_json
        report = metrics.get("report", "")
        if report and len(report.strip()) > 100:
            return {"report": report, "format": "xhtml", "execution_id": execution_id}
    
    # Try to get from evidence bundle
    evidence_path = execution.get("evidence_bundle_path")
    if evidence_path:
        try:
            import json
            with open(evidence_path, 'r') as f:
                evidence = json.load(f)
                metadata = evidence.get("execution_metadata", {})
                report_path = metadata.get("report_path")
                if report_path:
                    with open(report_path, 'r', encoding='utf-8') as rf:
                        return {"report": rf.read(), "format": "xhtml", "execution_id": execution_id}
        except Exception as e:
            print(f"Error loading report from evidence: {e}")
    
    # Generate report on-the-fly if not found
    try:
        pipeline = db.get_pipeline(execution["pipeline_id"])
        if pipeline:
            import json
            esg_standard = None
            if pipeline.get("esg_standard_id"):
                esg_standard = db.get_esg_standard(pipeline["esg_standard_id"])
            
            metrics = json.loads(metrics_json) if metrics_json else {}
            report = report_service.generate_report(
                execution_id=execution_id,
                metrics=metrics,
                schema=json.loads(pipeline["schema_json"]),
                assumptions=json.loads(pipeline["normalization_json"]),
                pipeline_name=pipeline["name"],
                esg_standard=esg_standard
            )
            return {"report": report, "format": "xhtml", "execution_id": execution_id}
    except Exception as e:
        print(f"Error generating report: {e}")
    
    raise HTTPException(status_code=404, detail="Report not found for this execution")

@app.get("/api/executions/{execution_id}/download-report")
async def download_execution_report(
    execution_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Download ESG report as HTML file."""
    report_data = await get_execution_report(execution_id, current_user)

    from fastapi.responses import Response
    return Response(
        content=report_data["report"],
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="esg_report_{execution_id}.html"'
        }
    )

# Blockchain endpoints (protected)
@app.post("/api/blockchain/anchor/{execution_id}")
async def anchor_execution(
    execution_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Anchor execution to blockchain."""
    execution = db.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.get("anchor_tx_id"):
        return {
            "tx_id": execution["anchor_tx_id"],
            "status": "already_anchored",
            "message": "Execution already anchored"
        }
    
    try:
        # Build Merkle tree from transformed data records
        from merkle import MerkleBatch
        import pandas as pd
        
        # Load transformed data
        gold_path = execution.get("output_file_path")
        if not gold_path:
            raise HTTPException(status_code=400, detail="No transformed data found")
        
        df = pd.read_csv(gold_path)
        records = df.to_dict('records')
        
        # Build Merkle tree
        batch = MerkleBatch(f"exec_{execution_id}")
        for record in records:
            batch.add_record(record)
        
        root_hash = batch.build_tree()
        batch_info = batch.get_batch_info()
        
        # Anchor Merkle root to blockchain
        if not blockchain:
            raise HTTPException(status_code=500, detail="Blockchain not initialized")
        
        anchor_result = blockchain.anchor_merkle_root(
            root_hash=root_hash,
            batch_id=batch_info["batch_id"],
            record_count=batch_info["record_count"]
        )
        
        # Save batch data for proof generation
        batch_data = {
            "batch_id": batch_info["batch_id"],
            "records": records,
            "leaf_hashes": batch.leaf_hashes,
            "root_hash": root_hash,
            "execution_id": execution_id
        }
        storage.save_batch_data(batch_info["batch_id"], batch_data)
        
        # Update execution with anchor
        db.update_execution(
            execution_id=execution_id,
            anchor_tx_id=anchor_result["tx_id"]
        )
        
        # Save anchor metadata
        storage.save_anchor_metadata(anchor_result["tx_id"], anchor_result)
        
        # Create anchor record
        db.create_anchor(
            execution_id=execution_id,
            tx_id=anchor_result["tx_id"],
            anchor_type="merkle_batch",
            data_hash=anchor_result["root_hash"],
            block_id=anchor_result.get("block_id")
        )
        
        return {
            "tx_id": anchor_result["tx_id"],
            "block_id": anchor_result.get("block_id"),
            "root_hash": anchor_result["root_hash"],
            "batch_id": batch_info["batch_id"],
            "record_count": batch_info["record_count"],
            "status": anchor_result["status"]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to anchor: {str(e)}")

@app.get("/api/blockchain/verify/{tx_id}")
async def verify_anchor(
    tx_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Verify blockchain anchor."""
    try:
        result = blockchain.verify_anchor(tx_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify: {str(e)}")

@app.get("/api/blockchain/anchor/{execution_id}/status")
async def get_anchor_status(
    execution_id: int,
    current_user: dict = Depends(get_current_user)
):
    """Get anchor status for execution."""
    execution = db.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if not execution.get("anchor_tx_id"):
        return {
            "anchored": False,
            "message": "Execution not anchored"
        }
    
    try:
        verification = blockchain.verify_anchor(execution["anchor_tx_id"])
        return {
            "anchored": True,
            "tx_id": execution["anchor_tx_id"],
            "verification": verification
        }
    except Exception as e:
        return {
            "anchored": True,
            "tx_id": execution["anchor_tx_id"],
            "verification": {
                "confirmed": False,
                "error": str(e)
            }
        }

# File downloads (protected)
@app.get("/api/files/{file_path:path}")
async def download_file(
    file_path: str,
    current_user: dict = Depends(get_current_user)
):
    """Download a file."""
    file = storage.get_file(file_path)
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(str(file))

if __name__ == "__main__":
    import sqlite3
    uvicorn.run(app, host="0.0.0.0", port=8000)

