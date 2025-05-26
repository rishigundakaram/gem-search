#!/usr/bin/env python3
"""
Helper script to run tests with proper path setup.
"""

import os
import sys
import pytest

if __name__ == "__main__":
    # Add the parent directory to the path to properly resolve imports
    search_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'search')
    if search_dir not in sys.path:
        sys.path.insert(0, search_dir)
    
    # Exit with the pytest return code
    sys.exit(pytest.main(['-v', 'search/tests/crawler/test_utils.py']))