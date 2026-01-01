"""
API endpoints for Merkle proof generation and verification.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))

from database import Database
from storage import StorageManager
from merkle import MerkleBatch, verify_proof, hash_record
from middleware import get_current_user

router = APIRouter(prefix="/api/proof", tags=["proof"])

db = Database()
storage = StorageManager()


@router.get("/batch/{batch_id}/record/{record_index}")
async def get_record_proof(
    batch_id: str,
    record_index: int,
    current_user: dict = Depends(get_current_user)
):
    """Get Merkle proof for a specific record in a batch."""
    # Load batch data
    batch_data = storage.get_batch_data(batch_id)
    if not batch_data:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    # Check access (user must own the execution)
    execution_id = batch_data.get("execution_id")
    if execution_id:
        execution = db.get_execution(execution_id)
        if execution:
            # Check if user owns this execution (unless admin)
            if current_user.get("role") != "admin" and execution.get("executed_by") != current_user["username"]:
                raise HTTPException(status_code=403, detail="Access denied")
    
    if record_index >= len(batch_data["records"]):
        raise HTTPException(status_code=400, detail="Record index out of range")
    
    # Reconstruct batch
    batch = MerkleBatch(batch_id)
    batch.records = batch_data["records"]
    batch.leaf_hashes = batch_data["leaf_hashes"]
    batch.root_hash = batch_data["root_hash"]
    batch.build_tree()
    
    # Get proof
    proof = batch.get_proof(record_index)
    record = batch.records[record_index]
    record_hash = batch.leaf_hashes[record_index]
    
    return {
        "batch_id": batch_id,
        "record_index": record_index,
        "record_hash": record_hash,
        "proof": proof,
        "root_hash": batch.root_hash,
        "canonical_record": record,
        "verification_instructions": {
            "step1": "Compute hash of canonical record",
            "step2": "Use proof path to compute Merkle root",
            "step3": "Verify computed root matches anchored root_hash",
            "step4": "Check root_hash exists on blockchain via tx_id"
        }
    }


@router.post("/verify")
async def verify_record_proof(
    record: Dict,
    proof: list,
    root_hash: str,
    current_user: dict = Depends(get_current_user)
):
    """Verify a Merkle proof for a record."""
    # Hash the record
    record_hash = hash_record(record)
    
    # Verify proof
    is_valid = verify_proof(record_hash, proof, root_hash)
    
    return {
        "valid": is_valid,
        "record_hash": record_hash,
        "root_hash": root_hash,
        "message": "Proof is valid" if is_valid else "Proof is invalid"
    }

