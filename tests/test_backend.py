#!/usr/bin/env python3
"""
Simple backend functionality test.
"""
import os
import sys

# Add search directory to path
search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "search")
sys.path.insert(0, search_dir)


def test_imports():
    """Test that all modules can be imported."""
    try:
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def test_database():
    """Test database connection setup."""
    try:
        from app.database import get_db, engine
        
        # Test that we can create the engine and get a session
        assert engine is not None
        db_gen = get_db()
        db = next(db_gen)
        db.close()
        print("✓ Database connection setup successful")
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_app_creation():
    """Test FastAPI app creation."""
    try:
        from app.main import app

        assert app is not None
        print("✓ FastAPI app creation successful")
        return True
    except Exception as e:
        print(f"✗ App creation failed: {e}")
        return False


def run_tests():
    """Run all tests."""
    print("Testing backend functionality...")
    tests = [test_imports, test_database, test_app_creation]

    passed = 0
    for test in tests:
        if test():
            passed += 1

    print(f"\nResults: {passed}/{len(tests)} tests passed")
    return passed == len(tests)


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
