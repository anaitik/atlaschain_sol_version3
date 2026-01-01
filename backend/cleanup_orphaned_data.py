"""
Script to clean up orphaned data (pipelines and executions without valid users).
This should be run periodically or after user deletions.
"""
import sys
from pathlib import Path

backend_dir = Path(__file__).parent
root_dir = backend_dir.parent
sys.path.insert(0, str(root_dir))

from database import Database
import sqlite3

def cleanup_orphaned_data():
    """Remove pipelines and executions that don't belong to any valid user."""
    db = Database()
    conn = db.get_connection()
    cursor = conn.cursor()
    
    # Get all valid usernames
    cursor.execute("SELECT username FROM users WHERE is_active = 1")
    valid_users = {row[0] for row in cursor.fetchall()}
    valid_users.add("system")  # Keep system-created items
    
    print(f"Found {len(valid_users)} valid users")
    
    # Find orphaned pipelines
    cursor.execute("SELECT id, name, created_by FROM pipelines")
    orphaned_pipelines = []
    for row in cursor.fetchall():
        pipeline_id, name, created_by = row
        if created_by and created_by not in valid_users:
            orphaned_pipelines.append((pipeline_id, name, created_by))
    
    print(f"Found {len(orphaned_pipelines)} orphaned pipelines")
    
    # Find orphaned executions
    cursor.execute("SELECT id, pipeline_id, executed_by FROM pipeline_executions")
    orphaned_executions = []
    for row in cursor.fetchall():
        exec_id, pipeline_id, executed_by = row
        if executed_by and executed_by not in valid_users:
            orphaned_executions.append((exec_id, pipeline_id, executed_by))
    
    print(f"Found {len(orphaned_executions)} orphaned executions")
    
    # Ask for confirmation
    if orphaned_pipelines or orphaned_executions:
        print("\nOrphaned pipelines:")
        for pid, name, creator in orphaned_pipelines:
            print(f"  - Pipeline #{pid}: {name} (created by: {creator})")
        
        print("\nOrphaned executions:")
        for eid, pid, executor in orphaned_executions:
            print(f"  - Execution #{eid} (pipeline: {pid}, executed by: {executor})")
        
        response = input("\nDelete orphaned data? (yes/no): ")
        if response.lower() == "yes":
            # Delete orphaned executions first (they reference pipelines)
            for eid, _, _ in orphaned_executions:
                cursor.execute("DELETE FROM pipeline_executions WHERE id = ?", (eid,))
                print(f"Deleted execution #{eid}")
            
            # Delete orphaned pipelines
            for pid, _, _ in orphaned_pipelines:
                cursor.execute("DELETE FROM pipelines WHERE id = ?", (pid,))
                print(f"Deleted pipeline #{pid}")
            
            conn.commit()
            print(f"\nCleanup complete: Removed {len(orphaned_pipelines)} pipelines and {len(orphaned_executions)} executions")
        else:
            print("Cleanup cancelled")
    else:
        print("No orphaned data found. Database is clean!")
    
    conn.close()

if __name__ == "__main__":
    cleanup_orphaned_data()

