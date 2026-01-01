"""
Authentication and authorization module.
"""
import sys
from pathlib import Path

# Add parent directory to path
backend_dir = Path(__file__).parent
root_dir = backend_dir.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import sqlite3

try:
    from jose import JWTError, jwt as jose_jwt
    JWT_AVAILABLE = True
except ImportError:
    # Fallback to simple JWT if jose not available
    import base64
    import json
    import time
    
    JWT_AVAILABLE = False
    
    class JWTError(Exception):
        pass
    
    class SimpleJWT:
        @staticmethod
        def encode(payload: dict, secret: str, algorithm: str) -> str:
            """Simple JWT encoding."""
            header = {"alg": algorithm, "typ": "JWT"}
            payload["iat"] = int(time.time())
            header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
            payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
            signature = hashlib.sha256(f"{header_b64}.{payload_b64}.{secret}".encode()).hexdigest()
            return f"{header_b64}.{payload_b64}.{signature}"
        
        @staticmethod
        def decode(token: str, secret: str, algorithms: list) -> dict:
            """Simple JWT decoding."""
            try:
                parts = token.split(".")
                if len(parts) != 3:
                    raise JWTError("Invalid token")
                payload_b64 = parts[1]
                payload_b64 += "=" * (4 - len(payload_b64) % 4)
                payload = json.loads(base64.urlsafe_b64decode(payload_b64))
                
                # Verify expiration
                if "exp" in payload and payload["exp"] < time.time():
                    raise JWTError("Token expired")
                
                return payload
            except Exception as e:
                raise JWTError(f"Invalid token: {str(e)}")
    
    jose_jwt = SimpleJWT()

from database import Database
from config import SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ADMIN_PASSWORD

# JWT Configuration
ALGORITHM = "HS256"

# Password hashing (using SHA-256 for simplicity, use bcrypt in production)


class AuthService:
    """Service for authentication and authorization."""
    
    def __init__(self, db: Database):
        self.db = db
        self._init_admin_user()
    
    def _init_admin_user(self):
        """Initialize admin user if not exists."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE username = ?", ("AtlasChainLTD",))
        admin = cursor.fetchone()
        
        if not admin:
            # Create admin user (password sourced from env variable). If ADMIN_PASSWORD is not set,
            # skip auto-creating an admin and print a warning so operator can create one manually.
            if not ADMIN_PASSWORD:
                print("Warning: ADMIN_PASSWORD not set. Skipping auto-creation of admin user. Please create an admin account manually.")
                conn.close()
                return

            password_hash = self.hash_password(ADMIN_PASSWORD)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, is_approved, is_active, full_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "AtlasChainLTD",
                "admin@atlaschain.com",
                password_hash,
                "admin",
                1,  # Auto-approved
                1,  # Active
                "AtlasChain Admin"
            ))
            conn.commit()
        
        conn.close()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        # Using SHA-256 for simplicity (use bcrypt in production)
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password."""
        return AuthService.hash_password(plain_password) == hashed_password
    
    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: str = ""
    ) -> Dict:
        """
        Register a new user (pending approval).
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Check if username or email already exists
        cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Username or email already exists")
        
        # Check if pending registration exists
        cursor.execute("SELECT id FROM user_registrations WHERE username = ? OR email = ?", (username, email))
        if cursor.fetchone():
            conn.close()
            raise ValueError("Registration already pending")
        
        # Create pending registration
        password_hash = self.hash_password(password)
        cursor.execute("""
            INSERT INTO user_registrations (username, email, password_hash, full_name, status)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, password_hash, full_name, "pending"))
        
        registration_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "registration_id": registration_id,
            "username": username,
            "status": "pending",
            "message": "Registration submitted. Waiting for admin approval."
        }
    
    def approve_user(self, registration_id: int, approved_by: int) -> Dict:
        """
        Approve a user registration.
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        # Get registration
        cursor.execute("SELECT * FROM user_registrations WHERE id = ?", (registration_id,))
        registration = cursor.fetchone()
        
        if not registration:
            conn.close()
            raise ValueError("Registration not found")
        
        if registration[5] != "pending":  # status column
            conn.close()
            raise ValueError(f"Registration already {registration[5]}")
        
        # Create user - check which columns exist first
        cursor.execute("PRAGMA table_info(users)")
        available_columns = [row[1] for row in cursor.fetchall()]
        
        # Build insert query dynamically
        columns = ["username", "email", "password_hash", "role", "is_approved", "is_active"]
        values = [
            registration[1],  # username
            registration[2],  # email
            registration[3],  # password_hash
            "user",
            1,  # is_approved
            1   # is_active
        ]
        
        if "full_name" in available_columns:
            columns.append("full_name")
            values.append(registration[4] if len(registration) > 4 else "")
        
        if "approved_by" in available_columns:
            columns.append("approved_by")
            values.append(approved_by)
        
        if "approved_at" in available_columns:
            columns.append("approved_at")
            values.append(datetime.utcnow())
        
        placeholders = ["?"] * len(values)
        cursor.execute(f"""
            INSERT INTO users ({", ".join(columns)})
            VALUES ({", ".join(placeholders)})
        """, tuple(values))
        
        user_id = cursor.lastrowid
        
        # Update registration status
        cursor.execute("""
            UPDATE user_registrations 
            SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
            WHERE id = ?
        """, ("approved", approved_by, registration_id))
        
        conn.commit()
        conn.close()
        
        return {
            "user_id": user_id,
            "username": registration[1],
            "status": "approved"
        }
    
    def reject_user(self, registration_id: int, reviewed_by: int) -> Dict:
        """Reject a user registration."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE user_registrations 
            SET status = ?, reviewed_at = CURRENT_TIMESTAMP, reviewed_by = ?
            WHERE id = ?
        """, ("rejected", reviewed_by, registration_id))
        
        conn.commit()
        conn.close()
        
        return {"status": "rejected"}
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """
        Authenticate a user and return user info if successful.
        """
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, password_hash, role, is_approved, is_active, full_name
            FROM users 
            WHERE username = ? AND is_active = 1
        """, (username,))
        
        user = cursor.fetchone()
        conn.close()
        
        if not user:
            return None
        
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        if not user["is_approved"]:
            return None
        
        return {
            "id": user["id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"],
            "full_name": user["full_name"]
        }
    
    def create_access_token(self, user_data: Dict) -> str:
        """Create JWT access token."""
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode = {
            "sub": str(user_data["id"]),
            "username": user_data["username"],
            "role": user_data["role"],
            "exp": expire.timestamp() if JWT_AVAILABLE else int(datetime.utcnow().timestamp()) + (ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        }
        encoded_jwt = jose_jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token and return user data."""
        try:
            payload = jose_jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
            username = payload.get("username")
            role = payload.get("role")
            
            if user_id is None:
                return None
            
            return {
                "id": int(user_id),
                "username": username,
                "role": role
            }
        except JWTError:
            return None
    
    def get_pending_registrations(self) -> List[Dict]:
        """Get all pending user registrations."""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, full_name, created_at, status
            FROM user_registrations
            WHERE status = 'pending'
            ORDER BY created_at DESC
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_user(self, user_id: int) -> Optional[Dict]:
        """Get user by ID."""
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, username, email, role, is_approved, is_active, full_name, created_at
            FROM users
            WHERE id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None

