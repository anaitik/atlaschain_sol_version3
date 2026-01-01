"""
Code Generation Agent - Generates transformation code and ESG reports.
"""
from llm.llm_client import ask_llm
from typing import Dict


class CodeGenAgent:
    """Agent for generating transformation code."""
    
    async def run(self, schema: Dict, normalization: Dict, metric_intent: Dict, dataset_id: str) -> str:
        """
        Generate transformation code.
        
        Args:
            schema: Inferred schema
            normalization: Normalization and assumptions
            metric_intent: Metric design
            dataset_id: Dataset identifier
        
        Returns:
            Python code string
        """
        system_prompt = """
You are a senior data engineering agent. Please act as expert, think hard this pipeline will transform data.

You write safe, auditable Python code for ESG and risk analytics pipelines.

You also prepare report which can directly be submitted.

You MAY use external libraries ONLY if:
- They are explicitly imported
- They are widely used, stable, and appropriate for the task
- Installation commands are clearly provided
- Failures degrade gracefully without hallucinating data

Hard constraints:
- No file I/O
- No printing or logging
- No silent network calls
- No fabricated data
- All derived columns must be traceable to inputs

If required inputs or services are unavailable, return null values.

Return ONLY executable Python code and dependency installation commands.
"""
        user_prompt = f"""
You are given a dataset schema, normalization rules, and an ESG enrichment objective.

Your task is to generate Python code that enriches the dataset with
ROW-LEVEL ESG-relevant derived columns.
You have to do reasoning which new columns should be added.
Work like a real human person who looks at raw data cleans it, transform it and generate final data which can directly be used for generating audit reports.
Interpret each Row and think what columns can be added which will make it real audit report.
Also report should be XHTML based real report and save it.

Schema:
{schema}

Normalization & Assumptions:
{normalization}

ESG enrichment objective:
{metric_intent}

You MAY use external libraries (e.g., geopy), but must follow these rules:

- All external dependencies must be listed in a dedicated `dependencies` section
- Dependencies must be installable via pip
- Network-based features (e.g., geocoding) must be optional and fail-safe
- If geocoding fails or inputs are ambiguous, derived columns must be null
- Never fabricate coordinates or distances

Required function signature:

def run_pipeline(df):
    ...
    return results

Return structure:
results must be:
{{
  "metrics": {{metric_id: scalar_value}},
  "data": transformed_dataframe,
  "report": "XHTML report string"
}}

The report should be a proper ESG standards-based report in XHTML format that can be directly submitted to auditors.
Include sections for:
- Executive Summary
- Data Quality Assessment
- ESG Metrics Calculated
- Risk Analysis
- Evidence and Assumptions
- Compliance Status

Output constraints (strict):
- Return valid JSON only
- No markdown
- No explanations
- Exactly two top-level keys:
  - "dependencies"
  - "code"

Output format:
{{
  "dependencies": [
    "pip install geopy"
  ],
  "code": "def run_pipeline(df): ..."
}}
"""
        code = await ask_llm(system_prompt, user_prompt)
        return code.get("code", code) if isinstance(code, dict) else code
