#!/usr/bin/env python3
"""Quick test of step 06"""

import sys
from pathlib import Path

# Add step-06 to path
sys.path.insert(0, str(Path(__file__).parent / 'step-06-extract-and-link-symbols'))

# Import the module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "extract_symbols",
    Path(__file__).parent / 'step-06-extract-and-link-symbols' / 'extract-symbols.py'
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

print("Running Step 06...")
print()

try:
    module.main()
    print("\n✓ Step 06 completed!")
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
