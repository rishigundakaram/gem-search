#!/usr/bin/env python3
"""
Local test runner script that mimics CI/CD pipeline.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description, cwd=None):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {description} - PASSED")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Run all tests locally."""
    root_dir = Path(__file__).parent.parent
    backend_dir = root_dir / "backend"
    frontend_dir = root_dir / "frontend"
    
    print("🚀 Running Gem Search CI/CD Pipeline Locally")
    print(f"Root directory: {root_dir}")
    
    success = True
    
    # Install Poetry dependencies
    if not run_command(["poetry", "install"], "Installing Python dependencies", cwd=root_dir):
        success = False
    
    # Initialize database
    if not run_command(["poetry", "run", "python", "init_db.py"], "Initializing database", cwd=backend_dir):
        success = False
    
    # Run backend unit tests
    if not run_command(["poetry", "run", "pytest", "backend/tests/", "-v"], "Backend unit tests", cwd=root_dir):
        success = False
    
    # Run integration tests
    if not run_command(["poetry", "run", "pytest", "tests/", "-v"], "Integration tests", cwd=root_dir):
        success = False
    
    # Run linting
    if not run_command(["poetry", "run", "ruff", "check", "backend/", "tests/"], "Ruff linting", cwd=root_dir):
        success = False
    
    # Run formatting check
    if not run_command(["poetry", "run", "black", "--check", "backend/", "tests/"], "Black formatting", cwd=root_dir):
        success = False
    
    # Frontend tests (if npm is available)
    if (frontend_dir / "package.json").exists():
        print(f"\n🔄 Installing frontend dependencies")
        if not run_command(["npm", "ci"], "Frontend dependency installation", cwd=frontend_dir):
            success = False
        
        if not run_command(["npm", "test", "--", "--watchAll=false"], "Frontend tests", cwd=frontend_dir):
            success = False
        
        if not run_command(["npm", "run", "build"], "Frontend build", cwd=frontend_dir):
            success = False
    
    # Summary
    print(f"\n{'='*50}")
    if success:
        print("🎉 All tests passed! Ready for CI/CD")
        sys.exit(0)
    else:
        print("💥 Some tests failed. Check output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()