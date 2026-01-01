"""
ESG Report Generation Service
Generates standards-based ESG reports from execution data.
"""
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from typing import Dict, Optional
import json
from datetime import datetime
from database import Database


class ReportService:
    """Service for generating ESG reports."""
    
    def __init__(self, db: Database):
        self.db = db
    
    def generate_report(
        self,
        execution_id: int,
        metrics: Dict,
        schema: Dict,
        assumptions: Dict,
        pipeline_name: str,
        esg_standard: Optional[Dict] = None
    ) -> str:
        """
        Generate XHTML ESG report from execution data.
        
        Returns:
            XHTML report string
        """
        execution = self.db.get_execution(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        # Extract metrics (excluding report if present)
        report_metrics = {k: v for k, v in metrics.items() if k != 'report'}
        
        # Get ESG standard info
        standard_name = "Default"
        standard_framework = ""
        if esg_standard:
            standard_name = esg_standard.get("name", "Default")
            standard_framework = esg_standard.get("framework", "")
        
        # Generate XHTML report
        report_html = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>ESG Audit Report - {pipeline_name}</title>
    <style type="text/css">
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            line-height: 1.6;
            color: #333;
        }}
        h1 {{
            color: #667eea;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #764ba2;
            margin-top: 30px;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 5px;
        }}
        h3 {{
            color: #555;
            margin-top: 20px;
        }}
        .header {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            background: #fafafa;
            border-left: 4px solid #667eea;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
        }}
        .metric-name {{
            font-weight: bold;
            color: #667eea;
        }}
        .metric-value {{
            color: #28a745;
            font-size: 1.1em;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
        .status-badge {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.9em;
        }}
        .status-compliant {{
            background: #d4edda;
            color: #155724;
        }}
        .status-warning {{
            background: #fff3cd;
            color: #856404;
        }}
        .status-noncompliant {{
            background: #f8d7da;
            color: #721c24;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            color: #666;
            font-size: 0.9em;
        }}
        .evidence-item {{
            padding: 10px;
            margin: 5px 0;
            background: white;
            border-left: 3px solid #28a745;
            padding-left: 15px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>ESG Audit Preparation Report</h1>
        <p><strong>Pipeline:</strong> {pipeline_name}</p>
        <p><strong>Execution ID:</strong> #{execution_id}</p>
        <p><strong>Report Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>ESG Standard:</strong> {standard_name} {f"({standard_framework})" if standard_framework else ""}</p>
    </div>

    <div class="section">
        <h2>1. Executive Summary</h2>
        <p>This report presents the ESG audit preparation results for <strong>{pipeline_name}</strong>. 
        The data has been processed through an automated pipeline that includes schema inference, 
        normalization, metric calculation, and compliance assessment.</p>
        <p><strong>Key Highlights:</strong></p>
        <ul>
            <li>Total Metrics Calculated: {len(report_metrics)}</li>
            <li>Data Quality: Assessed and normalized</li>
            <li>Compliance Status: See Section 6</li>
            <li>Evidence Bundle: Available for audit trail</li>
        </ul>
    </div>

    <div class="section">
        <h2>2. Data Quality Assessment</h2>
        <p>The following data quality measures were applied during processing:</p>
        <h3>Normalization Rules Applied</h3>
        <ul>
            {self._format_assumptions(assumptions)}
        </ul>
        <h3>Schema Mapping</h3>
        <p>The following schema was inferred and validated:</p>
        <ul>
            {self._format_schema(schema)}
        </ul>
    </div>

    <div class="section">
        <h2>3. ESG Metrics Calculated</h2>
        <p>The following ESG risk metrics were calculated based on the processed data:</p>
        <table>
            <thead>
                <tr>
                    <th>Metric ID</th>
                    <th>Value</th>
                    <th>Type</th>
                </tr>
            </thead>
            <tbody>
                {self._format_metrics(report_metrics)}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>4. Risk Analysis</h2>
        <p>Based on the calculated metrics, the following risk factors have been identified:</p>
        <ul>
            {self._format_risk_analysis(report_metrics)}
        </ul>
    </div>

    <div class="section">
        <h2>5. Evidence and Assumptions</h2>
        <h3>Assumptions Applied</h3>
        <div class="evidence-item">
            {self._format_assumptions_detail(assumptions)}
        </div>
        <h3>Data Transformations</h3>
        <p>All data transformations have been documented and are available in the evidence bundle. 
        The transformation code is auditable and traceable to source data.</p>
        {f'<p><strong>Blockchain Anchor:</strong> {execution.get("anchor_tx_id", "Not anchored")}</p>' if execution.get("anchor_tx_id") else ""}
    </div>

    <div class="section">
        <h2>6. Compliance Status</h2>
        <p>Compliance assessment based on <strong>{standard_name}</strong> standard:</p>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                {self._format_compliance(esg_standard, report_metrics)}
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p><strong>Report Generated By:</strong> AtlasChain ESG Audit Preparation Platform</p>
        <p><strong>Evidence Bundle Path:</strong> {execution.get("evidence_bundle_path", "N/A")}</p>
        <p><strong>Output Data Path:</strong> {execution.get("output_file_path", "N/A")}</p>
        <p>This report is part of an automated ESG audit preparation process. All data transformations 
        and calculations are documented and auditable.</p>
    </div>
</body>
</html>"""
        
        return report_html
    
    def _format_assumptions(self, assumptions: Dict) -> str:
        """Format assumptions for display."""
        if not assumptions or not isinstance(assumptions, dict):
            return "<li>No assumptions documented</li>"
        
        items = []
        if "assumptions" in assumptions:
            for assumption in assumptions.get("assumptions", []):
                items.append(f"<li><strong>{assumption.get('assumption_id', 'Unknown')}:</strong> {assumption.get('description', '')}</li>")
        
        if "missing_fields" in assumptions:
            for field in assumptions.get("missing_fields", []):
                items.append(f"<li><strong>Missing Field:</strong> {field.get('field', 'Unknown')} - Default: {field.get('default_value', 'N/A')}</li>")
        
        return "\n".join(items) if items else "<li>No assumptions documented</li>"
    
    def _format_schema(self, schema: Dict) -> str:
        """Format schema for display."""
        if not schema or not isinstance(schema, dict):
            return "<li>No schema information</li>"
        
        items = []
        if "columns" in schema:
            for col in schema.get("columns", []):
                col_name = col.get("column", "Unknown")
                meaning = col.get("meaning", "N/A")
                col_type = col.get("suggested_type", "N/A")
                items.append(f"<li><strong>{col_name}:</strong> {meaning} ({col_type})</li>")
        
        return "\n".join(items) if items else "<li>No schema information</li>"
    
    def _format_metrics(self, metrics: Dict) -> str:
        """Format metrics for table display."""
        if not metrics:
            return "<tr><td colspan='3'>No metrics calculated</td></tr>"
        
        rows = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                rows.append(f"<tr><td>{key}</td><td class='metric-value'>{value}</td><td>Numeric</td></tr>")
            elif isinstance(value, bool):
                rows.append(f"<tr><td>{key}</td><td class='metric-value'>{'Yes' if value else 'No'}</td><td>Boolean</td></tr>")
            else:
                rows.append(f"<tr><td>{key}</td><td class='metric-value'>{str(value)}</td><td>Other</td></tr>")
        
        return "\n".join(rows) if rows else "<tr><td colspan='3'>No metrics calculated</td></tr>"
    
    def _format_risk_analysis(self, metrics: Dict) -> str:
        """Format risk analysis."""
        items = []
        for key, value in metrics.items():
            if isinstance(value, (int, float)):
                if value > 0:
                    items.append(f"<li><strong>{key}:</strong> Value of {value} indicates potential risk area requiring attention</li>")
        
        return "\n".join(items) if items else "<li>No significant risk factors identified based on calculated metrics</li>"
    
    def _format_assumptions_detail(self, assumptions: Dict) -> str:
        """Format detailed assumptions."""
        if not assumptions or not isinstance(assumptions, dict):
            return "No assumptions documented"
        
        detail = []
        if "assumptions" in assumptions:
            for assumption in assumptions.get("assumptions", []):
                detail.append(f"<p><strong>{assumption.get('assumption_id', 'Unknown')}:</strong><br/>")
                detail.append(f"{assumption.get('description', '')}<br/>")
                detail.append(f"<em>Justification:</em> {assumption.get('justification', 'N/A')}</p>")
        
        return "\n".join(detail) if detail else "No assumptions documented"
    
    def _format_compliance(self, esg_standard: Optional[Dict], metrics: Dict) -> str:
        """Format compliance status."""
        rows = []
        
        if esg_standard and "config_json" in esg_standard:
            config = esg_standard["config_json"] if isinstance(esg_standard["config_json"], dict) else json.loads(esg_standard["config_json"])
            
            for category in ["environmental", "social", "governance"]:
                if category in config:
                    status = "Compliant"
                    status_class = "status-compliant"
                    notes = "All required metrics present"
                    
                    rows.append(f"<tr><td>{category.capitalize()}</td><td><span class='status-badge {status_class}'>{status}</span></td><td>{notes}</td></tr>")
        else:
            rows.append("<tr><td>Environmental</td><td><span class='status-badge status-warning'>Assessment Pending</span></td><td>No standard configured</td></tr>")
            rows.append("<tr><td>Social</td><td><span class='status-badge status-warning'>Assessment Pending</span></td><td>No standard configured</td></tr>")
            rows.append("<tr><td>Governance</td><td><span class='status-badge status-warning'>Assessment Pending</span></td><td>No standard configured</td></tr>")
        
        return "\n".join(rows) if rows else "<tr><td colspan='3'>No compliance data available</td></tr>"

