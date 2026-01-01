"""
Local file storage management for AtlasChain.
Manages bronze/silver/gold data lake structure and evidence bundles.
"""
from pathlib import Path
from typing import Optional
from datetime import datetime
import json
import shutil


class StorageManager:
    """Manages local file storage with data lake structure."""
    
    def __init__(self, base_path: str = "storage"):
        # Use backend/storage directory
        backend_dir = Path(__file__).parent
        self.base_path = backend_dir / base_path
        self._init_storage()
    
    def _init_storage(self):
        """Initialize storage directory structure."""
        directories = [
            "bronze",      # Raw input data
            "silver",      # Transformed data
            "gold",        # Final output data
            "uploads",     # User uploaded files
            "evidence",    # Evidence bundles
            "anchors",     # Anchor metadata
            "schemas",     # Schema definitions
            "assumptions", # Assumption definitions
            "reports",     # ESG reports
        ]
        
        for dir_name in directories:
            (self.base_path / dir_name).mkdir(parents=True, exist_ok=True)
    
    def save_upload(self, file_content: bytes, filename: str) -> str:
        """Save uploaded file to bronze layer."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_filename = filename.replace(" ", "_")
        file_path = self.base_path / "uploads" / f"{timestamp}_{safe_filename}"
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        return str(file_path)
    
    def save_bronze(self, file_path: str, execution_id: int) -> str:
        """Save file to bronze layer with execution ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source = Path(file_path)
        dest = self.base_path / "bronze" / f"{timestamp}_input.csv"
        
        shutil.copy2(source, dest)
        return str(dest)
    
    def save_silver(self, df_data: any, execution_id: int) -> str:
        """Save transformed data to silver layer."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.base_path / "silver" / f"{timestamp}_transformed.csv"
        
        if hasattr(df_data, 'to_csv'):
            df_data.to_csv(dest, index=False)
        else:
            import pandas as pd
            pd.DataFrame(df_data).to_csv(dest, index=False)
        
        return str(dest)
    
    def save_gold(self, df_data: any, execution_id: int) -> str:
        """Save final output to gold layer."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.base_path / "gold" / f"{timestamp}_output.csv"
        
        if hasattr(df_data, 'to_csv'):
            df_data.to_csv(dest, index=False)
        else:
            import pandas as pd
            pd.DataFrame(df_data).to_csv(dest, index=False)
        
        return str(dest)
    
    def save_evidence_bundle(
        self,
        execution_id: int,
        schema: dict,
        assumptions: dict,
        metrics: dict,
        transform_code: str,
        execution_metadata: dict
    ) -> str:
        """Save evidence bundle for audit trail."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.base_path / "evidence" / f"{timestamp}_evidence.json"
        
        evidence = {
            "execution_id": execution_id,
            "timestamp": timestamp,
            "schema": schema,
            "assumptions": assumptions,
            "metrics": metrics,
            "transform_code": transform_code,
            "execution_metadata": execution_metadata
        }
        
        with open(dest, "w") as f:
            json.dump(evidence, f, indent=2)
        
        return str(dest)
    
    def save_anchor_metadata(self, tx_id: str, anchor_data: dict) -> str:
        """Save anchor metadata."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = self.base_path / "anchors" / f"{timestamp}_anchor.json"
        
        anchor_metadata = {
            "tx_id": tx_id,
            "timestamp": timestamp,
            **anchor_data
        }
        
        with open(dest, "w") as f:
            json.dump(anchor_metadata, f, indent=2)
        
        return str(dest)
    
    def save_report(self, execution_id: int, report_content: str) -> str:
        """Save ESG report to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reports_dir = self.base_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        dest = reports_dir / f"{timestamp}_execution_{execution_id}_report.html"
        
        with open(dest, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        return str(dest)
    
    def get_file(self, file_path: str) -> Optional[Path]:
        """Get file path if it exists."""
        path = Path(file_path)
        if path.exists():
            return path
        return None
    
    def save_batch_data(self, batch_id: str, batch_data) -> str:
        """Save Merkle batch data for proof generation."""
        batch_dir = self.base_path / "batches"
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = batch_dir / f"{batch_id}_data.json"
        with open(file_path, 'w') as f:
            json.dump(batch_data, f, indent=2)
        
        return str(file_path)
    
    def get_batch_data(self, batch_id: str):
        """Load Merkle batch data."""
        batch_file = self.base_path / "batches" / f"{batch_id}_data.json"
        if batch_file.exists():
            with open(batch_file, 'r') as f:
                return json.load(f)
        return None

