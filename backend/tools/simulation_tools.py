"""
Simulation Tools - Simulate Assumption, Preview Metric Impact
"""
from typing import Dict, List, Any
import pandas as pd


class SimulationTools:
    """Tools for simulating assumptions and metric impacts."""
    
    @staticmethod
    def simulate_assumption(
        data: pd.DataFrame,
        assumption: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Simulate the impact of an assumption on data.
        
        Args:
            data: Input dataframe
            assumption: {
                "field": "field_name",
                "default_value": value,
                "condition": optional condition
            }
        
        Returns:
            Dataframe with assumption applied
        """
        df = data.copy()
        field = assumption.get("field")
        default_value = assumption.get("default_value")
        condition = assumption.get("condition")
        
        if field:
            if condition:
                # Apply conditionally
                mask = eval(condition, {"df": df, "pd": pd})
                df.loc[mask, field] = df.loc[mask, field].fillna(default_value)
            else:
                # Apply to all nulls
                df[field] = df[field].fillna(default_value)
        
        return df
    
    @staticmethod
    def preview_metric_impact(
        original_data: pd.DataFrame,
        transformed_data: pd.DataFrame,
        metrics: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Preview the impact of transformations on metrics.
        
        Returns:
            Comparison of original vs transformed metrics
        """
        return {
            "original_row_count": len(original_data),
            "transformed_row_count": len(transformed_data),
            "metrics": metrics,
            "columns_added": list(set(transformed_data.columns) - set(original_data.columns)),
            "columns_removed": list(set(original_data.columns) - set(transformed_data.columns))
        }

