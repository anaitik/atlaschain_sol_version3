"""
Schema Inference Agent - Infers semantic meaning of columns from data.
"""
import pandas as pd
from llm.llm_client import ask_llm
from typing import Dict, List, Any


class SchemaAgent:
    """Agent for inferring data schema."""
    
    async def run(self, headers: List[str], rows: List[List], dataset_id: str) -> Dict:
        """
        Run schema inference.
        
        Args:
            headers: Column headers
            rows: Sample rows of data
            dataset_id: Dataset identifier
        
        Returns:
            Schema dictionary
        """
        # Convert rows to dict format for LLM
        samples = []
        for row in rows[:5]:  # First 5 rows
            sample = {}
            for i, header in enumerate(headers):
                if i < len(row):
                    sample[header] = row[i]
            samples.append(sample)
        
        system_prompt = """
You are a data analyst. 
Infer semantic meaning of columns.
Do NOT invent standards.
Just describe what each column represents.
"""

        user_prompt = f"""
Columns:
{headers}

Sample rows:
{samples}

Output format:
Return JSON only.
No markdown. No commentary.
No additional text.

{{
  "columns": [
    {{
      "column": "...",
      "meaning": "...",
      "suggested_type": "string|number|location|entity"
    }}
  ]
}}
"""
        return await ask_llm(system_prompt, user_prompt)
