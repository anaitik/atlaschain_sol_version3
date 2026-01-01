"""
Algorand blockchain integration for anchoring ESG audit data.
Anchors only Merkle roots, not actual data.
"""
from typing import Dict, Optional
import hashlib
import json
import os
from algosdk import account, mnemonic, transaction
from algosdk.v2client import algod
import base64


class AlgorandAnchor:
    """Algorand blockchain anchoring service for Merkle roots."""
    
    def __init__(
        self,
        algod_token: str = "",
        algod_address: str = None,
        network: str = "testnet",
        sender_address: str = None,
        sender_mnemonic: str = None
    ):
        """
        Initialize Algorand client with credentials.
        
        Credentials can be provided via:
        1. Constructor parameters
        2. Environment variables (ALGORAND_ADDRESS, ALGORAND_MNEMONIC)
        
        For production, use mainnet:
        - algod_address: "https://mainnet-api.algonode.cloud"
        - network: "mainnet"
        """
        self.algod_address = algod_address or os.getenv("ALGONODE_URL", "https://testnet-api.algonode.cloud")
        self.algod_token = algod_token or os.getenv("ALGOD_TOKEN", "")
        self.network = network
        
        # Get sender credentials
        self.sender_address = sender_address or os.getenv("ALGORAND_ADDRESS")
        self.sender_mnemonic = sender_mnemonic or os.getenv("ALGORAND_MNEMONIC")
        
        if not self.sender_address or not self.sender_mnemonic:
            raise ValueError(
                "Algorand credentials required. Set ALGORAND_ADDRESS and ALGORAND_MNEMONIC "
                "environment variables or pass to constructor."
            )
        
        # Initialize client
        if self.algod_token:
            self.algod_client = algod.AlgodClient(self.algod_token, self.algod_address)
        else:
            # Public node (no token needed for testnet)
            self.algod_client = algod.AlgodClient("", self.algod_address)
        
        # Get private key from mnemonic
        try:
            self.sender_private_key = mnemonic.to_private_key(self.sender_mnemonic)
        except Exception as e:
            raise ValueError(f"Invalid mnemonic: {e}")
    
    def _generate_account(self) -> Dict[str, str]:
        """Generate a new Algorand account (for testing)."""
        private_key, address = account.generate_account()
        return {
            "address": address,
            "private_key": private_key.hex(),
            "mnemonic": mnemonic.from_private_key(private_key)
        }
    
    def anchor_merkle_root(
        self,
        root_hash: str,
        batch_id: str,
        record_count: int = 0
    ) -> Dict[str, str]:
        """
        Anchor Merkle root to Algorand blockchain.
        
        Only the Merkle root is anchored, not the actual data.
        Format: ATLAS|BATCH:{batch_id}|ROOT:{root_hash}|COUNT:{record_count}
        
        Args:
            root_hash: Merkle root hash (hex string)
            batch_id: Batch identifier
            record_count: Number of records in batch
        
        Returns:
            Dictionary with tx_id, block_id, and status
        """
        try:
            # Get suggested params
            params = self.algod_client.suggested_params()
            
            # Create note with format: ATLAS|BATCH:{batch_id}|ROOT:{root_hash}|COUNT:{count}
            note_text = f"ATLAS|BATCH:{batch_id}|ROOT:{root_hash}|COUNT:{record_count}"
            note_bytes = note_text.encode()[:1000]  # Algorand note limit
            
            # Create transaction (0 ALGO payment to self)
            txn = transaction.PaymentTxn(
                sender=self.sender_address,
                sp=params,
                receiver=self.sender_address,  # Send to self (zero amount)
                amt=0,
                note=note_bytes
            )
            
            # Sign transaction
            signed_txn = txn.sign(self.sender_private_key)
            
            # Send transaction
            tx_id = self.algod_client.send_transaction(signed_txn)
            
            # Wait for confirmation (4 rounds)
            confirmed_txn = transaction.wait_for_confirmation(
                self.algod_client, tx_id, 4
            )
            
            return {
                "tx_id": tx_id,
                "block_id": str(confirmed_txn.get("confirmed-round", "")),
                "root_hash": root_hash,
                "batch_id": batch_id,
                "record_count": record_count,
                "status": "confirmed"
            }
        
        except Exception as e:
            raise RuntimeError(f"Failed to anchor Merkle root to blockchain: {str(e)}")
    
    def verify_anchor(self, tx_id: str) -> Optional[Dict]:
        """
        Verify an anchor by transaction ID.
        Extracts Merkle root and batch info from transaction note.
        
        Uses pending_transaction_info which works for both pending and 
        recently confirmed transactions. For older transactions, consider
        using Algorand Indexer API.
        """
        try:
            # Use pending_transaction_info (works for pending and recently confirmed)
            txn_info = self.algod_client.pending_transaction_info(tx_id)
            
            # Check if transaction is confirmed
            confirmed_round = txn_info.get("confirmed-round", 0)
            confirmed = confirmed_round > 0
            
            if not confirmed:
                # Transaction is still pending
                return {
                    "tx_id": tx_id,
                    "confirmed": False,
                    "status": "pending",
                    "message": "Transaction is pending confirmation"
                }
            
            # Extract note from transaction
            # Structure: txn_info['txn']['txn']['note'] or txn_info['txn']['note']
            note_b64 = None
            txn_data = txn_info.get("txn", {})
            
            if isinstance(txn_data, dict):
                # Try nested structure (common in algosdk)
                inner_txn = txn_data.get("txn", {})
                if inner_txn and isinstance(inner_txn, dict):
                    note_b64 = inner_txn.get("note")
                else:
                    note_b64 = txn_data.get("note")
            
            # Decode note
            note = ""
            batch_id = None
            root_hash = None
            record_count = None
            
            if note_b64:
                try:
                    if isinstance(note_b64, str):
                        note_bytes = base64.b64decode(note_b64)
                    else:
                        note_bytes = base64.b64decode(note_b64)
                    note = note_bytes.decode('utf-8')
                    
                    # Parse note: ATLAS|BATCH:{batch_id}|ROOT:{root_hash}|COUNT:{count}
                    parts = note.split("|")
                    
                    for part in parts:
                        if part.startswith("BATCH:"):
                            batch_id = part.split(":", 1)[1]
                        elif part.startswith("ROOT:"):
                            root_hash = part.split(":", 1)[1]
                        elif part.startswith("COUNT:"):
                            record_count = int(part.split(":", 1)[1])
                except Exception as decode_error:
                    note = f"Error decoding note: {decode_error}"
            
            return {
                "tx_id": tx_id,
                "confirmed": True,
                "block": confirmed_round,
                "note": note,
                "batch_id": batch_id,
                "root_hash": root_hash,
                "record_count": record_count,
                "timestamp": txn_info.get("round-time")
            }
        except Exception as e:
            error_msg = str(e)
            
            # Return error with helpful message and explorer link
            return {
                "tx_id": tx_id,
                "confirmed": False,
                "error": error_msg,
                "explorer_url": f"https://testnet.algoexplorer.io/tx/{tx_id}",
                "message": f"Could not verify transaction. This may be an older transaction. Check Algorand Explorer: https://testnet.algoexplorer.io/tx/{tx_id}"
            }
    
    def get_anchor_status(self, tx_id: str) -> Dict:
        """Get status of an anchor transaction."""
        return self.verify_anchor(tx_id)

