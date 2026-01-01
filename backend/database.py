"""
Database models and connection management using SQLite.
"""
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import json


class Database:
    """SQLite database manager for AtlasChain."""
    
    def __init__(self, db_path: str = "atlaschain.db"):
        # Use backend directory for database
        backend_dir = Path(__file__).parent
        self.db_path = str(backend_dir / db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Pipelines table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipelines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                description TEXT,
                schema_json TEXT,
                normalization_json TEXT,
                metric_intent_json TEXT,
                transform_code TEXT,
                esg_standard_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by TEXT,
                version TEXT DEFAULT '1.0.0',
                is_active BOOLEAN DEFAULT 1,
                FOREIGN KEY (esg_standard_id) REFERENCES esg_standards(id)
            )
        """)
        
        # ESG Standards table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS esg_standards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                region TEXT,
                framework TEXT,
                config_json TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        
        # Pipeline Executions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pipeline_executions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pipeline_id INTEGER NOT NULL,
                input_file_path TEXT,
                output_file_path TEXT,
                evidence_bundle_path TEXT,
                anchor_tx_id TEXT,
                status TEXT,
                metrics_json TEXT,
                error_message TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                executed_by TEXT,
                FOREIGN KEY (pipeline_id) REFERENCES pipelines(id)
            )
        """)
        
        # Users table with authentication
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT DEFAULT 'user',
                is_approved BOOLEAN DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP,
                approved_by INTEGER,
                FOREIGN KEY (approved_by) REFERENCES users(id)
            )
        """)
        
        # User registrations (pending approvals)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_registrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                reviewed_by INTEGER,
                FOREIGN KEY (reviewed_by) REFERENCES users(id)
            )
        """)
        
        # Anchors table (blockchain records)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS anchors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id INTEGER,
                tx_id TEXT NOT NULL UNIQUE,
                block_id TEXT,
                network TEXT DEFAULT 'algorand',
                anchor_type TEXT,
                data_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (execution_id) REFERENCES pipeline_executions(id)
            )
        """)
        
        conn.commit()
        
        # Migrate existing databases - add missing columns
        self._migrate_schema(conn)
        
        conn.close()
    
    def _migrate_schema(self, conn):
        """Migrate existing database schema to add missing columns."""
        cursor = conn.cursor()
        
        # Check if users table exists and has password_hash column
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='users'
        """)
        if cursor.fetchone():
            # Check if password_hash column exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add missing columns one by one
            columns_to_add = [
                ('password_hash', 'TEXT'),
                ('full_name', 'TEXT'),
                ('role', "TEXT DEFAULT 'user'"),
                ('is_approved', 'BOOLEAN DEFAULT 0'),
                ('is_active', 'BOOLEAN DEFAULT 1'),
                ('approved_at', 'TIMESTAMP'),
                ('approved_by', 'INTEGER')
            ]
            
            added_any = False
            for col_name, col_def in columns_to_add:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                        print(f"Added column: {col_name}")
                        added_any = True
                    except sqlite3.OperationalError as e:
                        print(f"Migration note for {col_name}: {e}")
            
            # Try to add updated_at separately (SQLite doesn't allow DEFAULT CURRENT_TIMESTAMP in ALTER TABLE)
            if 'updated_at' not in columns:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
                    print("Added column: updated_at")
                    added_any = True
                except sqlite3.OperationalError as e:
                    print(f"Migration note for updated_at: {e}")
            
            if added_any:
                conn.commit()
                print("Database schema migrated: Added authentication columns to users table")
        
        # Check if user_registrations table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_registrations'
        """)
        if not cursor.fetchone():
            # Create user_registrations table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_registrations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    full_name TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_at TIMESTAMP,
                    reviewed_by INTEGER,
                    FOREIGN KEY (reviewed_by) REFERENCES users(id)
                )
            """)
            conn.commit()
            print("Database schema migrated: Created user_registrations table")
        
        # Check if anchors table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='anchors'
        """)
        if not cursor.fetchone():
            # Create anchors table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS anchors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER,
                    tx_id TEXT NOT NULL UNIQUE,
                    block_id TEXT,
                    network TEXT DEFAULT 'algorand',
                    anchor_type TEXT,
                    data_hash TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (execution_id) REFERENCES pipeline_executions(id)
                )
            """)
            conn.commit()
            print("Database schema migrated: Created anchors table")
    
    def get_connection(self):
        """Get database connection."""
        return sqlite3.connect(self.db_path)
    
    def create_pipeline(
        self,
        name: str,
        schema_json: Dict,
        normalization_json: Dict,
        metric_intent_json: Dict,
        transform_code: str,
        esg_standard_id: Optional[int] = None,
        description: str = "",
        created_by: str = "system"
    ) -> int:
        """Create a new pipeline."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pipelines 
            (name, description, schema_json, normalization_json, metric_intent_json, 
             transform_code, esg_standard_id, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            name,
            description,
            json.dumps(schema_json),
            json.dumps(normalization_json),
            json.dumps(metric_intent_json),
            transform_code,
            esg_standard_id,
            created_by
        ))
        
        pipeline_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return pipeline_id
    
    def get_pipeline(self, pipeline_id: int) -> Optional[Dict]:
        """Get pipeline by ID."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pipelines WHERE id = ?", (pipeline_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def list_pipelines(self, is_active: bool = True, created_by: Optional[str] = None, user_role: Optional[str] = None) -> List[Dict]:
        """List pipelines. If created_by is provided, filter by creator. Admins see all."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_role == "admin":
            # Admins see all pipelines
            cursor.execute("SELECT * FROM pipelines WHERE is_active = ? ORDER BY created_at DESC", (is_active,))
        elif created_by:
            # Regular users see only their own pipelines
            cursor.execute("SELECT * FROM pipelines WHERE is_active = ? AND created_by = ? ORDER BY created_at DESC", (is_active, created_by))
        else:
            # Default: show all (for backward compatibility)
            cursor.execute("SELECT * FROM pipelines WHERE is_active = ? ORDER BY created_at DESC", (is_active,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def create_esg_standard(
        self,
        name: str,
        config_json: Dict,
        region: str = "",
        framework: str = "",
        description: str = ""
    ) -> int:
        """Create a new ESG standard configuration."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO esg_standards 
            (name, region, framework, config_json, description)
            VALUES (?, ?, ?, ?, ?)
        """, (
            name,
            region,
            framework,
            json.dumps(config_json),
            description
        ))
        
        standard_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return standard_id
    
    def get_esg_standard(self, standard_id: int) -> Optional[Dict]:
        """Get ESG standard by ID."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM esg_standards WHERE id = ?", (standard_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def list_esg_standards(self) -> List[Dict]:
        """List all ESG standards."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM esg_standards WHERE is_active = 1 ORDER BY name")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def create_execution(
        self,
        pipeline_id: int,
        input_file_path: str,
        status: str = "running",
        executed_by: str = "system"
    ) -> int:
        """Create a new pipeline execution record."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO pipeline_executions 
            (pipeline_id, input_file_path, status, executed_by)
            VALUES (?, ?, ?, ?)
        """, (pipeline_id, input_file_path, status, executed_by))
        
        execution_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return execution_id
    
    def update_execution(
        self,
        execution_id: int,
        status: str = None,
        output_file_path: str = None,
        evidence_bundle_path: str = None,
        anchor_tx_id: str = None,
        metrics_json: Dict = None,
        error_message: str = None
    ):
        """Update pipeline execution."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        if output_file_path:
            updates.append("output_file_path = ?")
            params.append(output_file_path)
        if evidence_bundle_path:
            updates.append("evidence_bundle_path = ?")
            params.append(evidence_bundle_path)
        if anchor_tx_id:
            updates.append("anchor_tx_id = ?")
            params.append(anchor_tx_id)
        if metrics_json:
            updates.append("metrics_json = ?")
            params.append(json.dumps(metrics_json))
        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)
        
        if updates:
            updates.append("completed_at = CURRENT_TIMESTAMP")
            params.append(execution_id)
            
            query = f"UPDATE pipeline_executions SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        conn.close()
    
    def list_executions(self, pipeline_id: Optional[int] = None, executed_by: Optional[str] = None, user_role: Optional[str] = None) -> List[Dict]:
        """List pipeline executions. Filter by user unless admin."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if user_role == "admin":
            # Admins see all executions
            if pipeline_id:
                cursor.execute("SELECT * FROM pipeline_executions WHERE pipeline_id = ? ORDER BY started_at DESC", (pipeline_id,))
            else:
                cursor.execute("SELECT * FROM pipeline_executions ORDER BY started_at DESC")
        elif executed_by:
            # Regular users see only their own executions
            if pipeline_id:
                cursor.execute("SELECT * FROM pipeline_executions WHERE pipeline_id = ? AND executed_by = ? ORDER BY started_at DESC", (pipeline_id, executed_by))
            else:
                cursor.execute("SELECT * FROM pipeline_executions WHERE executed_by = ? ORDER BY started_at DESC", (executed_by,))
        else:
            # Default: show all (for backward compatibility)
            if pipeline_id:
                cursor.execute("SELECT * FROM pipeline_executions WHERE pipeline_id = ? ORDER BY started_at DESC", (pipeline_id,))
            else:
                cursor.execute("SELECT * FROM pipeline_executions ORDER BY started_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_execution(self, execution_id: int) -> Optional[Dict]:
        """Get execution by ID."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pipeline_executions WHERE id = ?", (execution_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def create_anchor(
        self,
        execution_id: int,
        tx_id: str,
        anchor_type: str,
        data_hash: str,
        block_id: str = None,
        network: str = "algorand"
    ) -> int:
        """Create an anchor record."""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO anchors 
            (execution_id, tx_id, block_id, network, anchor_type, data_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (execution_id, tx_id, block_id, network, anchor_type, data_hash))
        
        anchor_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return anchor_id

