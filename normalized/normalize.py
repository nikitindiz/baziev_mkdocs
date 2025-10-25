#!/usr/bin/env python3
"""
Normalize Python file

Wrapper script that calls the main extraction script.
This ensures the script can be run from the normalize.py location.
"""

import sys
from pathlib import Path

# Add step directory to path
step_dir = Path(__file__).parent / 'step-06-extract-and-link-symbols'
sys.path.insert(0, str(step_dir))

# Import and run main script
from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location(
    "extract_symbols",
    step_dir / "extract-symbols.py"
)
extract_symbols = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extract_symbols)

if __name__ == '__main__':
    extract_symbols.main()
