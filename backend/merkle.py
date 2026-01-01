"""
Merkle tree implementation for ESG data anchoring.
Only the Merkle root is anchored to blockchain, not the actual data.
"""
import json
import hashlib
from typing import List, Dict, Tuple, Optional
from decimal import Decimal


def canonicalize(record: dict) -> str:
    """
    Canonicalize a record for consistent hashing.
    
    Rules:
    - Keys sorted
    - Fixed numeric precision (6 decimal places)
    - ISO timestamps
    - Stable schema
    - No null field drift
    - No white-space variation
    """
    def normalize(value):
        if isinstance(value, float):
            # Fixed precision
            return format(Decimal(str(value)), ".6f")
        if isinstance(value, dict):
            # Recursively normalize dicts with sorted keys
            return {k: normalize(value[k]) for k in sorted(value)}
        if isinstance(value, list):
            # Normalize lists
            return [normalize(item) for item in value]
        if value is None:
            return None
        return value
    
    normalized = normalize(record)
    # JSON with no whitespace, sorted keys
    return json.dumps(normalized, separators=(",", ":"), sort_keys=True, ensure_ascii=False)


def hash_record(record: dict) -> str:
    """Hash a canonicalized record."""
    canonical = canonicalize(record)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_pair(a: str, b: str) -> str:
    """Hash two hashes together (for Merkle tree internal nodes)."""
    return hashlib.sha256((a + b).encode()).hexdigest()


def build_merkle_tree(leaves: List[str]) -> Tuple[List[List[str]], str]:
    """
    Build a Merkle tree from leaf hashes.
    
    Args:
        leaves: List of leaf hashes (record hashes)
    
    Returns:
        Tuple of (tree levels, root hash)
    """
    if len(leaves) == 0:
        return [], ""
    
    if len(leaves) == 1:
        return [leaves], leaves[0]
    
    level = leaves.copy()
    tree = [level]
    
    while len(level) > 1:
        # If odd number of nodes, duplicate the last one
        if len(level) % 2 == 1:
            level.append(level[-1])
        
        # Create parent level
        level = [
            hash_pair(level[i], level[i + 1])
            for i in range(0, len(level), 2)
        ]
        tree.append(level)
    
    return tree, level[0]


def generate_proof(tree: List[List[str]], leaf_index: int) -> List[Tuple[str, str]]:
    """
    Generate Merkle proof for a leaf at given index.
    
    Args:
        tree: Merkle tree (list of levels)
        leaf_index: Index of the leaf in the first level
    
    Returns:
        List of (sibling_hash, position) tuples for proof path
        position is 'left' or 'right'
    """
    if not tree or leaf_index >= len(tree[0]):
        return []
    
    proof = []
    index = leaf_index
    
    for level in tree[:-1]:  # All levels except root
        sibling_index = index ^ 1  # XOR to get sibling
        
        if sibling_index < len(level):
            # Determine position
            position = "right" if index % 2 == 0 else "left"
            proof.append((level[sibling_index], position))
        
        index //= 2  # Move to parent level
    
    return proof


def verify_proof(leaf_hash: str, proof: List[Tuple[str, str]], root_hash: str) -> bool:
    """
    Verify a Merkle proof.
    
    Args:
        leaf_hash: Hash of the record
        proof: List of (sibling_hash, position) tuples
        root_hash: Expected Merkle root
    
    Returns:
        True if proof is valid
    """
    current = leaf_hash
    
    for sibling_hash, position in proof:
        if position == "left":
            # Sibling is on left, current is on right
            current = hash_pair(sibling_hash, current)
        else:
            # Sibling is on right, current is on left
            current = hash_pair(current, sibling_hash)
    
    return current == root_hash


class MerkleBatch:
    """Manages a batch of records for Merkle tree anchoring."""
    
    def __init__(self, batch_id: str):
        self.batch_id = batch_id
        self.records: List[Dict] = []
        self.leaf_hashes: List[str] = []
        self.tree: Optional[List[List[str]]] = None
        self.root_hash: Optional[str] = None
    
    def add_record(self, record: dict) -> int:
        """
        Add a record to the batch.
        
        Returns:
            Index of the record in the batch
        """
        record_hash = hash_record(record)
        index = len(self.records)
        
        self.records.append(record)
        self.leaf_hashes.append(record_hash)
        
        # Reset tree (will be rebuilt when needed)
        self.tree = None
        self.root_hash = None
        
        return index
    
    def build_tree(self) -> str:
        """Build Merkle tree and return root hash."""
        if not self.leaf_hashes:
            raise ValueError("Cannot build tree: no records in batch")
        
        if self.tree is None:
            self.tree, self.root_hash = build_merkle_tree(self.leaf_hashes)
        
        return self.root_hash
    
    def get_proof(self, record_index: int) -> List[Tuple[str, str]]:
        """Get Merkle proof for a record at given index."""
        if self.tree is None:
            self.build_tree()
        
        return generate_proof(self.tree, record_index)
    
    def verify_record(self, record: dict, record_index: int) -> bool:
        """Verify a record is in the batch."""
        if self.root_hash is None:
            self.build_tree()
        
        record_hash = hash_record(record)
        if record_index >= len(self.leaf_hashes) or self.leaf_hashes[record_index] != record_hash:
            return False
        
        proof = self.get_proof(record_index)
        return verify_proof(record_hash, proof, self.root_hash)
    
    def get_batch_info(self) -> Dict:
        """Get batch metadata."""
        if self.root_hash is None:
            self.build_tree()
        
        return {
            "batch_id": self.batch_id,
            "record_count": len(self.records),
            "root_hash": self.root_hash,
            "leaf_count": len(self.leaf_hashes)
        }

