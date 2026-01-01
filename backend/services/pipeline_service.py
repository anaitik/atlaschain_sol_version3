"""
Pipeline service - orchestrates agentic pipeline creation and execution.
"""
import sys
from pathlib import Path

# Add parent directory to path to import agents and llm modules
backend_dir = Path(__file__).parent.parent
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))


from typing import Dict, List, Optional
import pandas as pd
import importlib.util
import json
import os
# Agents imported in methods to avoid circular imports
from database import Database
from storage import StorageManager
from blockchain import AlgorandAnchor


class PipelineService:
    """Service for managing pipeline lifecycle."""
    
    def __init__(self, db: Database, storage: StorageManager, blockchain: AlgorandAnchor):
        self.db = db
        self.storage = storage
        self.blockchain = blockchain
    
    async def create_pipeline_from_sample(
        self,
        csv_path: str,
        pipeline_name: str,
        description: str = "",
        esg_standard_id: Optional[int] = None,
        created_by: str = "system"
    ) -> Dict:
        """
        Create a new pipeline from a sample CSV file.
        Orchestrates all agents in the reasoning plane.
        """
        # Read sample data
        df = pd.read_csv(csv_path)
        headers = list(df.columns)
        rows = df.head(5).values.tolist()
        
        # Step 1: Schema Inference Agent
        def _find_agents_dir(max_ascend: int = 10):
        # ascend from current file up to root looking for 'agents'
         cur = Path(__file__).resolve().parent
        tried = []
        for _ in range(max_ascend):
            candidate = cur / "agents"        # old
            candidate = cur.parent / "agents" # new
            tried.append(str(candidate))
            if candidate.exists():
                return candidate, tried
            parent = cur.parent
            if parent == cur:
                break
            cur = parent

        # try current working directory
        cwd_candidate = Path.cwd() / "agents"
        tried.append(str(cwd_candidate))
        if cwd_candidate.exists():
            return cwd_candidate, tried

        # common container paths
        for p in [Path("/app/agents"), Path("/workspace/agents"), Path("/agents")]:
            tried.append(str(p))
            if p.exists():
                return p, tried

        # environment override
        env_path = os.getenv("AGENTS_DIR")
        if env_path:
            env_candidate = Path(env_path)
            tried.append(str(env_candidate))
            if env_candidate.exists():
                return env_candidate, tried

        return None, tried


        def _import_agent(module_filename: str, class_name: str):
            # First try to import as a normal installed package (if PYTHONPATH is set)
            try:
                mod = importlib.import_module(f"agents.{module_filename}")
                return getattr(mod, class_name)
            except Exception:
                pass

            agents_dir, tried_paths = _find_agents_dir()
            attempted_paths = []
            if agents_dir:
                agent_file = agents_dir / f"{module_filename}.py"
                attempted_paths.append(str(agent_file))
                if agent_file.exists():
                    spec = importlib.util.spec_from_file_location(f"agents.{module_filename}", str(agent_file))
                    agent_mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(agent_mod)
                    # ensure agent module is importable as 'agents.*' for downstream imports
                    try:
                        sys.modules[f"agents.{module_filename}"] = agent_mod
                    except Exception:
                        pass
                    return getattr(agent_mod, class_name)

            # Nothing worked; raise with helpful message including all paths we tried
            full_attempts = tried_paths + attempted_paths
            print(f"DEBUG: attempted agent import paths: {full_attempts}")
            raise ModuleNotFoundError(
                f"Agents module not found. Tried: {full_attempts} and package import 'agents.{module_filename}'. "
                "Ensure the 'agents' package is present in the project root or PYTHONPATH, or set AGENTS_DIR env var to point to it."
            )

        SchemaAgent = _import_agent("schema_agent", "SchemaAgent")
        schema_agent = SchemaAgent()
        schema = await schema_agent.run(headers, rows, pipeline_name)

        # Step 2: Normalization & Assumptions Agent
        NormalizationAgent = _import_agent("normalization_agent", "NormalizationAgent")
        norm_agent = NormalizationAgent()
        normalization = await norm_agent.run(schema, pipeline_name)

        # Step 3: Metric Intent Agent
        MetricIntentAgent = _import_agent("metric_intent_agent", "MetricIntentAgent")
        metric_agent = MetricIntentAgent()
        metric_intent = await metric_agent.run(schema, pipeline_name)

        # Step 4: Code Generation Agent
        CodeGenAgent = _import_agent("codegen_agent", "CodeGenAgent")
        codegen_agent = CodeGenAgent()
        transform_code = await codegen_agent.run(schema, normalization, metric_intent, pipeline_name)
        
        # Save pipeline to database
        pipeline_id = self.db.create_pipeline(
            name=pipeline_name,
            schema_json=schema,
            normalization_json=normalization,
            metric_intent_json=metric_intent,
            transform_code=transform_code,
            esg_standard_id=esg_standard_id,
            description=description,
            created_by=created_by
        )
        
        return {
            "pipeline_id": pipeline_id,
            "name": pipeline_name,
            "schema": schema,
            "normalization": normalization,
            "metric_intent": metric_intent,
            "status": "created"
        }
    
    async def execute_pipeline(
        self,
        pipeline_id: int,
        input_csv_path: str,
        executed_by: str = "system",
        anchor_to_blockchain: bool = True
    ) -> Dict:
        """
        Execute a saved pipeline on input data.
        """
        # Get pipeline
        pipeline = self.db.get_pipeline(pipeline_id)
        if not pipeline:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        # Create execution record
        execution_id = self.db.create_execution(
            pipeline_id=pipeline_id,
            input_file_path=input_csv_path,
            status="running",
            executed_by=executed_by
        )
        
        try:
            # Save to bronze
            bronze_path = self.storage.save_bronze(input_csv_path, execution_id)
            
            # Load transform code
            transform_code = pipeline["transform_code"]
            
            # Execute in sandboxed environment
            results = self._execute_transform_code(transform_code, input_csv_path)
            
            # Extract results
            transformed_df = results.get("data")
            metrics = results.get("metrics", {})
            report = results.get("report", "")
            
            # Save to silver and gold
            self.storage.save_silver(transformed_df, execution_id)
            gold_path = self.storage.save_gold(transformed_df, execution_id)
            
            # Generate proper ESG report if not provided or incomplete
            if not report or len(report.strip()) < 100:
                import sys
                from pathlib import Path
                backend_dir = Path(__file__).parent.parent
                root_dir = backend_dir.parent
                if str(root_dir) not in sys.path:
                    sys.path.insert(0, str(root_dir))
                
                from services.report_service import ReportService
                report_service = ReportService(self.db)
                
                # Get ESG standard if available
                esg_standard = None
                if pipeline.get("esg_standard_id"):
                    esg_standard = self.db.get_esg_standard(pipeline["esg_standard_id"])
                
                report = report_service.generate_report(
                    execution_id=execution_id,
                    metrics=metrics,
                    schema=json.loads(pipeline["schema_json"]),
                    assumptions=json.loads(pipeline["normalization_json"]),
                    pipeline_name=pipeline["name"],
                    esg_standard=esg_standard
                )
            
            # Save report to file
            report_path = self.storage.save_report(execution_id, report)
            
            # Create evidence bundle
            evidence_path = self.storage.save_evidence_bundle(
                execution_id=execution_id,
                schema=json.loads(pipeline["schema_json"]),
                assumptions=json.loads(pipeline["normalization_json"]),
                metrics=metrics,
                transform_code=transform_code,
                execution_metadata={
                    "pipeline_id": pipeline_id,
                    "input_path": bronze_path,
                    "output_path": gold_path,
                    "report_path": report_path
                }
            )
            
            # Anchor to blockchain using Merkle tree
            anchor_tx_id = None
            if anchor_to_blockchain and self.blockchain:
                # Load transformed data for Merkle tree
                df = pd.read_csv(gold_path)
                
                # Convert DataFrame to list of records
                records = df.to_dict('records')
                
                # Build Merkle tree from records
                from merkle import MerkleBatch
                batch = MerkleBatch(f"exec_{execution_id}")
                for record in records:
                    batch.add_record(record)
                
                # Get Merkle root
                root_hash = batch.build_tree()
                batch_info = batch.get_batch_info()
                
                # Anchor Merkle root to blockchain
                anchor_result = self.blockchain.anchor_merkle_root(
                    root_hash=root_hash,
                    batch_id=batch_info["batch_id"],
                    record_count=batch_info["record_count"]
                )
                
                anchor_tx_id = anchor_result["tx_id"]
                
                # Save batch data for proof generation
                batch_data = {
                    "batch_id": batch_info["batch_id"],
                    "records": records,
                    "leaf_hashes": batch.leaf_hashes,
                    "root_hash": root_hash,
                    "execution_id": execution_id
                }
                self.storage.save_batch_data(batch_info["batch_id"], batch_data)
                
                # Save anchor metadata
                self.storage.save_anchor_metadata(anchor_tx_id, anchor_result)
                
                # Create anchor record in DB
                self.db.create_anchor(
                    execution_id=execution_id,
                    tx_id=anchor_tx_id,
                    anchor_type="merkle_batch",
                    data_hash=root_hash,
                    block_id=anchor_result.get("block_id")
                )
            
            # Store report in metrics_json for easy retrieval
            metrics_with_report = {**metrics, "report": report}
            
            # Update execution
            self.db.update_execution(
                execution_id=execution_id,
                status="completed",
                output_file_path=gold_path,
                evidence_bundle_path=evidence_path,
                anchor_tx_id=anchor_tx_id,
                metrics_json=metrics_with_report
            )
            
            return {
                "execution_id": execution_id,
                "status": "completed",
                "output_path": gold_path,
                "evidence_path": evidence_path,
                "anchor_tx_id": anchor_tx_id,
                "metrics": metrics,
                "report": report
            }
        
        except Exception as e:
            # Update execution with error
            self.db.update_execution(
                execution_id=execution_id,
                status="failed",
                error_message=str(e)
            )
            raise
    
    def _execute_transform_code(self, code: str, input_csv: str) -> Dict:
        """Execute transform code in sandboxed environment."""
        # Create temporary module
        import tempfile
        import sys
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_path = f.name
        
        try:
            # Load module
            spec = importlib.util.spec_from_file_location("pipeline_transform", temp_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            
            # Load data
            df = pd.read_csv(input_csv)
            
            # Execute pipeline
            results = mod.run_pipeline(df)
            
            # Cleanup
            Path(temp_path).unlink()
            
            return results
        
        except Exception as e:
            Path(temp_path).unlink()
            raise RuntimeError(f"Pipeline execution failed: {str(e)}")
    
    def _hash_file(self, file_path: str) -> str:
        """Generate hash of file."""
        import hashlib
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()

