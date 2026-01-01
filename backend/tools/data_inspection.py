"""
Data Inspection Tools - Get Headers, Sample Rows, Column Stats
"""
import pandas as pd
from typing import Dict, List, Any


class DataInspectionTools:
    """Tools for inspecting uploaded data."""
    
    @staticmethod
    def get_headers(csv_path: str) -> List[str]:
        """Get column headers from CSV."""
        df = pd.read_csv(csv_path, nrows=0)
        return list(df.columns)
    
    @staticmethod
    def get_sample_rows(csv_path: str, n: int = 5) -> List[Dict[str, Any]]:
        """Get sample rows from CSV."""
        df = pd.read_csv(csv_path, nrows=n)
        return df.to_dict(orient="records")
    
    @staticmethod
    def get_column_stats(csv_path: str) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each column."""
        df = pd.read_csv(csv_path)
        stats = {}
        
        for col in df.columns:
            col_data = df[col]
            col_stats = {
                "dtype": str(col_data.dtype),
                "non_null_count": col_data.notna().sum(),
                "null_count": col_data.isna().sum(),
                "unique_count": col_data.nunique()
            }
            
            if pd.api.types.is_numeric_dtype(col_data):
                col_stats.update({
                    "min": float(col_data.min()) if col_data.notna().any() else None,
                    "max": float(col_data.max()) if col_data.notna().any() else None,
                    "mean": float(col_data.mean()) if col_data.notna().any() else None,
                    "std": float(col_data.std()) if col_data.notna().any() else None
                })
            
            stats[col] = col_stats
        
        return stats

