#!/usr/bin/env python3
"""
Test script to verify yoyo-migrations setup works correctly.
"""
import os
import sqlite3
import subprocess
import tempfile
import shutil

def run_command(cmd, cwd=None):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def test_migrations():
    """Test the migration setup."""
    print("Testing yoyo-migrations setup...")
    
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        test_db = os.path.join(temp_dir, "test.db")
        
        # Copy migration files to temp directory
        search_dir = os.path.join(os.path.dirname(__file__), "search")
        temp_search_dir = os.path.join(temp_dir, "search")
        shutil.copytree(search_dir, temp_search_dir)
        
        # Update yoyo.ini to use test database
        yoyo_config = os.path.join(temp_search_dir, "yoyo.ini")
        with open(yoyo_config, 'w') as f:
            f.write(f"""[DEFAULT]
database = sqlite:///{test_db}
sources = migrations
verbosity = 1
batch_mode = on
""")
        
        print(f"Testing with database: {test_db}")
        
        # Test yoyo list (should show pending migrations)
        success, stdout, stderr = run_command("yoyo list", cwd=temp_search_dir)
        if success:
            print("✅ yoyo list - OK")
            print(f"   Output: {stdout.strip()}")
        else:
            print("❌ yoyo list - FAILED")
            print(f"   Error: {stderr}")
            return False
        
        # Test yoyo apply
        success, stdout, stderr = run_command("yoyo apply --batch", cwd=temp_search_dir)
        if success:
            print("✅ yoyo apply - OK")
        else:
            print("❌ yoyo apply - FAILED")
            print(f"   Error: {stderr}")
            return False
        
        # Verify database structure
        try:
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Check if tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['documents', 'document_content', 'yoyo_migration']
            for table in expected_tables:
                if table in tables:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
                    return False
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Database verification failed: {e}")
            return False
        
        # Test rollback
        success, stdout, stderr = run_command("yoyo rollback --batch", cwd=temp_search_dir)
        if success:
            print("✅ yoyo rollback - OK")
        else:
            print("❌ yoyo rollback - FAILED")
            print(f"   Error: {stderr}")
            return False
        
        print("\n🎉 All migration tests passed!")
        return True

if __name__ == "__main__":
    success = test_migrations()
    exit(0 if success else 1)