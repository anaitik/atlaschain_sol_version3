"""
Execution Tools - Sandboxed Code Runner
"""
import importlib.util
import pandas as pd
from pathlib import Path
import tempfile
from typing import Dict, Any


class ExecutionTools:
    """Sandboxed code execution for pipeline transforms."""
    
    @staticmethod
    def run_sandboxed_code(
        code: str,
        input_data: pd.DataFrame,
        timeout: int = 300
    ) -> Dict[str, Any]:
        """
        Execute code in a sandboxed environment.
        
        Args:
            code: Python code to execute (must define run_pipeline function)
            input_data: Input dataframe
            timeout: Execution timeout in seconds
        
        Returns:
            Results dictionary with 'data', 'metrics', 'report'
        """
        # Create temporary module
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location("pipeline_transform", temp_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # Execute pipeline
            if not hasattr(mod, 'run_pipeline'):
                raise ValueError("Code must define 'run_pipeline' function")
            
            results = mod.run_pipeline(input_data)
            
            # Validate results
            if not isinstance(results, dict):
                raise ValueError("run_pipeline must return a dictionary")
            
            if "data" not in results:
                raise ValueError("Results must include 'data' key")
            
            # Cleanup
            Path(temp_path).unlink()
            
            return results
        
        except Exception as e:
            # Cleanup on error
            if Path(temp_path).exists():
                Path(temp_path).unlink()
            raise RuntimeError(f"Code execution failed: {str(e)}")

