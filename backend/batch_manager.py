"""
Batch manager for ESG records with anchoring policies.
Handles batching rules: size threshold, time threshold, priority triggers.
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from merkle import MerkleBatch, hash_record


class BatchManager:
    """Manages batches of ESG records for anchoring."""
    
    def __init__(
        self,
        max_batch_size: int = 500,
        max_wait_time_minutes: int = 60,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize batch manager.
        
        Args:
            max_batch_size: Maximum records per batch before anchoring
            max_wait_time_minutes: Maximum wait time before anchoring
            storage_path: Path to store batch metadata
        """
        self.max_batch_size = max_batch_size
        self.max_wait_time = timedelta(minutes=max_wait_time_minutes)
        self.storage_path = storage_path or Path("backend/storage/batches")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Active batches (keyed by batch_id)
        self.active_batches: Dict[str, MerkleBatch] = {}
        self.batch_metadata: Dict[str, Dict] = {}
    
    def _generate_batch_id(self) -> str:
        """Generate a unique batch ID."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"batch_{timestamp}"
    
    def add_record(
        self,
        record: dict,
        priority: bool = False,
        batch_id: Optional[str] = None
    ) -> Dict:
        """
        Add a record to a batch.
        
        Args:
            record: ESG record dict
            priority: If True, triggers immediate anchoring
            batch_id: Optional batch ID (for late submissions)
        
        Returns:
            Dict with batch_id, record_index, and should_anchor flag
        """
        # Determine which batch to use
        if batch_id and batch_id in self.active_batches:
            # Late submission to existing batch (shouldn't happen, but handle it)
            batch = self.active_batches[batch_id]
        else:
            # Create new batch or use current active batch
            if not self.active_batches or priority:
                batch_id = self._generate_batch_id()
                batch = MerkleBatch(batch_id)
                self.active_batches[batch_id] = batch
                self.batch_metadata[batch_id] = {
                    "created_at": datetime.utcnow().isoformat(),
                    "priority": priority
                }
            else:
                # Use most recent batch
                batch_id = max(self.active_batches.keys())
                batch = self.active_batches[batch_id]
        
        # Add record
        record_index = batch.add_record(record)
        
        # Check if should anchor
        should_anchor = (
            priority or
            len(batch.records) >= self.max_batch_size or
            self._should_anchor_by_time(batch_id)
        )
        
        return {
            "batch_id": batch_id,
            "record_index": record_index,
            "should_anchor": should_anchor,
            "batch_size": len(batch.records)
        }
    
    def _should_anchor_by_time(self, batch_id: str) -> bool:
        """Check if batch should be anchored due to time threshold."""
        if batch_id not in self.batch_metadata:
            return False
        
        created_at = datetime.fromisoformat(self.batch_metadata[batch_id]["created_at"])
        return datetime.utcnow() - created_at >= self.max_wait_time
    
    def get_batch(self, batch_id: str) -> Optional[MerkleBatch]:
        """Get a batch by ID."""
        return self.active_batches.get(batch_id)
    
    def prepare_batch_for_anchoring(self, batch_id: str) -> Dict:
        """
        Prepare batch for anchoring (build Merkle tree).
        
        Returns:
            Dict with batch info including root_hash
        """
        if batch_id not in self.active_batches:
            raise ValueError(f"Batch {batch_id} not found")
        
        batch = self.active_batches[batch_id]
        root_hash = batch.build_tree()
        
        batch_info = batch.get_batch_info()
        batch_info.update(self.batch_metadata[batch_id])
        
        # Save batch metadata
        self._save_batch_metadata(batch_id, batch_info)
        
        return batch_info
    
    def finalize_batch(self, batch_id: str, tx_id: str, block_id: Optional[str] = None):
        """Mark batch as anchored and move to storage."""
        if batch_id not in self.active_batches:
            raise ValueError(f"Batch {batch_id} not found")
        
        batch = self.active_batches[batch_id]
        batch_info = batch.get_batch_info()
        batch_info.update(self.batch_metadata[batch_id])
        batch_info.update({
            "tx_id": tx_id,
            "block_id": block_id,
            "anchored_at": datetime.utcnow().isoformat(),
            "status": "anchored"
        })
        
        # Save finalized batch
        self._save_batch_metadata(batch_id, batch_info)
        
        # Save batch records for proof generation
        batch_file = self.storage_path / f"{batch_id}_records.json"
        with open(batch_file, 'w') as f:
            json.dump({
                "batch_id": batch_id,
                "records": batch.records,
                "leaf_hashes": batch.leaf_hashes,
                "root_hash": batch.root_hash
            }, f, indent=2)
        
        # Remove from active batches
        del self.active_batches[batch_id]
        del self.batch_metadata[batch_id]
    
    def get_record_proof(self, batch_id: str, record_index: int) -> Dict:
        """Get proof for a specific record in an anchored batch."""
        # Load batch from storage
        batch_file = self.storage_path / f"{batch_id}_records.json"
        if not batch_file.exists():
            raise ValueError(f"Batch {batch_id} not found in storage")
        
        with open(batch_file, 'r') as f:
            batch_data = json.load(f)
        
        # Reconstruct batch
        batch = MerkleBatch(batch_id)
        batch.records = batch_data["records"]
        batch.leaf_hashes = batch_data["leaf_hashes"]
        batch.root_hash = batch_data["root_hash"]
        batch.build_tree()
        
        if record_index >= len(batch.records):
            raise ValueError(f"Record index {record_index} out of range")
        
        proof = batch.get_proof(record_index)
        record = batch.records[record_index]
        record_hash = batch.leaf_hashes[record_index]
        
        return {
            "batch_id": batch_id,
            "record_index": record_index,
            "record_hash": record_hash,
            "proof": proof,
            "root_hash": batch.root_hash,
            "canonical_record": record
        }
    
    def _save_batch_metadata(self, batch_id: str, metadata: Dict):
        """Save batch metadata to file."""
        metadata_file = self.storage_path / f"{batch_id}_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_batch_metadata(self, batch_id: str) -> Optional[Dict]:
        """Load batch metadata from file."""
        metadata_file = self.storage_path / f"{batch_id}_metadata.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None

