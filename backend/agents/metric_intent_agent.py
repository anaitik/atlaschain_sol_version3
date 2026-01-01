"""
Metric Intent Agent - Designs ESG risk metrics based on schema.
"""
from llm.llm_client import ask_llm
from typing import Dict


class MetricIntentAgent:
    """Agent for designing ESG metrics."""
    
    async def run(self, schema: Dict, dataset_id: str) -> Dict:
        """
        Propose ESG metrics based on schema.
        
        Args:
            schema: Inferred schema
            dataset_id: Dataset identifier
        
        Returns:
            Metric intent dictionary
        """
        system_prompt = """
You are a senior ESG, enterprise risk, and supply-chain analytics architect.

You design decision-grade business and ESG risk metrics used by boards, auditors, and regulators.

You prioritize uncovering hidden fragility, structural dependency, concentration risk, exposure pathways, and resilience gaps.

You do not calculate values. You do not invent data. You design metrics only.
"""

        user_prompt = f"""
You are acting as an ESG and business risk analytics expert.

Your task is to design **decision-grade metrics** strictly based on the provided dataset schema.

Primary risk lenses (every metric must align to at least one):

- Dependency risk (single points of failure, critical reliance)
- Concentration risk (supplier, customer, geography, component, process)
- Exposure risk (operational, geographic, regulatory, supply-chain)
- Diversity & resilience (redundancy, substitutability, optionality)

Hard rules (violations are errors):

- Do NOT perform calculations.
- Do NOT infer or invent metric values.
- Do NOT assume data not listed in the schema.
- Design metrics only (no KPIs, no dashboards, no commentary).
- Each metric must reveal **non-obvious risk or fragility**, not surface-level counts.
- Avoid vanity or compliance-only metrics.

For every metric:

- Clearly state the **risk insight** it exposes and **why it matters for decisions**.
- Explicitly list the **exact columns required**.
- If the schema is insufficient, propose **new columns** that must be added.
- Metrics must be auditable, defensible, and suitable for ESG disclosures or risk committees.

Input:
Dataset schema:
{schema}

Output constraints (strict):

- Return valid JSON only.
- No markdown.
- No explanations outside the JSON.
- No extra keys.
- No trailing commas or comments.

Output format:
{{
  "metrics": [
    {{
      "metric_id": "snake_case_unique_identifier",
      "intent": "Concise explanation of the specific risk this metric exposes and why leadership should care",
      "required_columns": ["column_a", "column_b"],
      "output_type": "count | score | risk_band"
    }}
  ]
}}

Design these metrics as if they will be scrutinized by:

- ESG auditors
- Risk & compliance teams
- Supply-chain resilience analysts
- Executive leadership and board members
"""
        return await ask_llm(system_prompt, user_prompt)
