"""
Normalization & Assumptions Agent
Handles data normalization, missing field detection, and assumption management.
"""
from llm.llm_client import ask_llm
from typing import Dict, List, Any
import pandas as pd


class NormalizationAgent:
    """Agent for normalization and assumptions."""
    
    async def run(self, schema: Dict, dataset_id: str) -> Dict[str, Any]:
        """
        Analyze schema to identify normalization needs and assumptions.
        
        Args:
            schema: Inferred schema from SchemaAgent
            dataset_id: Dataset identifier
        
        Returns:
            Normalization and assumptions dictionary
        """
        system_prompt = """
You are a senior data quality and normalization expert specializing in ESG audit data preparation.

Your role is to:
1. Identify missing or incomplete fields in the dataset
2. Propose sensible defaults and assumptions
3. Define normalization rules for data consistency
4. Ensure data quality standards for audit readiness

You must be conservative and transparent - all assumptions must be clearly documented.
"""

        user_prompt = f"""
Analyze the following dataset schema to identify normalization needs and assumptions.

Schema:
{schema}

For each identified issue, provide:
1. Missing fields that need defaults
2. Data quality issues requiring normalization
3. Assumptions to apply (with justification)
4. Normalization rules (data type conversions, standardizations)

Output format (JSON only, no markdown):
{{
  "missing_fields": [
    {{
      "field": "field_name",
      "default_value": "default_value_or_null",
      "justification": "why this default is appropriate",
      "required": true/false
    }}
  ],
  "normalization_rules": [
    {{
      "field": "field_name",
      "rule_type": "type_conversion|standardization|validation|cleaning",
      "rule": "description of the normalization rule",
      "example": "before -> after"
    }}
  ],
  "assumptions": [
    {{
      "assumption_id": "unique_id",
      "description": "clear description of the assumption",
      "applies_to": ["field1", "field2"],
      "justification": "why this assumption is reasonable",
      "impact": "what this assumption affects"
    }}
  ],
  "data_quality_issues": [
    {{
      "issue": "description of the issue",
      "severity": "critical|warning|info",
      "affected_fields": ["field1"],
      "recommendation": "how to address"
    }}
  ]
}}
"""

        result = await ask_llm(system_prompt, user_prompt)
        return result
