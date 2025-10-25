#!/usr/bin/env python3
"""
Normalize - Run all normalization steps

This script runs all normalization steps in order:
- Step 01: Extract formulas
- Step 02: Extract tables
- Step 03: Extract illustrations
- Step 04: Parse missed db-keys and src
- Step 05: Extract and link quoted literature
- Step 06: Extract and link symbols

Usage:
    python3 normalize.py              # Run all steps
    python3 normalize.py 01           # Run only step 01
    python3 normalize.py 01 02 03     # Run steps 01, 02, 03
    python3 normalize.py 05 06        # Run steps 05 and 06
    python3 normalize.py --clean      # Clean and run all steps
    python3 normalize.py --clean 01   # Clean and run step 01
"""

import sys
import importlib.util
import shutil
from pathlib import Path
from typing import List


# Step definitions
STEPS = {
    '01': {
        'name': 'Extract Formulas',
        'dir': 'step-01-extract-all-formulas',
        'script': 'extract-formulas.py'
    },
    '02': {
        'name': 'Extract Tables',
        'dir': 'step-02-extract-all-tables',
        'script': 'extract-tables.py'
    },
    '03': {
        'name': 'Extract Illustrations',
        'dir': 'step-03-extract-all-illustrations',
        'script': 'extract-illustrations.py'
    },
    '04': {
        'name': 'Parse Missed DB Keys',
        'dir': 'step-04-parse-missed-db-keys-and-src',
        'script': 'parse-missed.py'
    },
    '05': {
        'name': 'Extract and Link Literature',
        'dir': 'step-05-extract-and-link-quoted-literature',
        'script': 'parse-refs.py'
    },
    '06': {
        'name': 'Extract and Link Symbols',
        'dir': 'step-06-extract-and-link-symbols',
        'script': 'extract-symbols.py'
    }
}


def clean_output_directories(base_dir: Path):
    """
    Remove and recreate output directories.
    
    Cleans:
    - normalized/formulas
    - normalized/illustrations
    - normalized/literature
    - normalized/tables
    - normalized/symbols
    """
    dirs_to_clean = [
        'formulas',
        'illustrations',
        'literature',
        'tables',
        'symbols'
    ]
    
    print()
    print("🧹 Cleaning output directories...")
    print()
    
    for dir_name in dirs_to_clean:
        dir_path = base_dir / dir_name
        
        if dir_path.exists():
            # Count files before deletion
            file_count = len(list(dir_path.glob('*')))
            
            # Remove directory
            shutil.rmtree(dir_path)
            print(f"  ✓ Removed {dir_name}/ ({file_count} files)")
        else:
            print(f"  ○ {dir_name}/ (not found, skipping)")
        
        # Recreate empty directory
        dir_path.mkdir(parents=True, exist_ok=True)
    
    print()
    print("✓ All output directories cleaned and recreated")
    print()


def print_header(text: str):
    """Print formatted header"""
    print()
    print("=" * 80)
    print(f"  {text}")
    print("=" * 80)
    print()


def print_step_header(step_num: str, step_name: str):
    """Print step header"""
    print()
    print("─" * 80)
    print(f"  STEP {step_num}: {step_name}")
    print("─" * 80)
    print()


def run_step(step_num: str, base_dir: Path) -> bool:
    """
    Run a single normalization step.
    
    Returns True if successful, False otherwise.
    """
    if step_num not in STEPS:
        print(f"✗ Unknown step: {step_num}")
        return False
    
    step_info = STEPS[step_num]
    step_dir = base_dir / step_info['dir']
    script_path = step_dir / step_info['script']
    
    # Check if step exists
    if not script_path.exists():
        print(f"✗ Step {step_num} not found: {script_path}")
        return False
    
    # Print step header
    print_step_header(step_num, step_info['name'])
    
    try:
        # Load and execute the step script
        spec = importlib.util.spec_from_file_location(
            f"step_{step_num}",
            script_path
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run main function
        if hasattr(module, 'main'):
            module.main()
            print(f"\n✓ Step {step_num} completed successfully")
            return True
        else:
            print(f"✗ Step {step_num} has no main() function")
            return False
            
    except Exception as e:
        print(f"\n✗ Step {step_num} failed with error:")
        print(f"  {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


def list_steps():
    """Print available steps"""
    print_header("AVAILABLE NORMALIZATION STEPS")
    
    for step_num, step_info in sorted(STEPS.items()):
        print(f"  Step {step_num}: {step_info['name']}")
        print(f"            {step_info['dir']}/{step_info['script']}")
        print()


def main():
    """Main entry point"""
    base_dir = Path(__file__).parent
    
    # Parse command line arguments
    clean_mode = False
    args = sys.argv[1:]
    
    # Check for --clean flag
    if '--clean' in args:
        clean_mode = True
        args = [arg for arg in args if arg != '--clean']
    
    if len(args) > 0:
        if args[0] in ['--help', '-h', 'help']:
            print(__doc__)
            list_steps()
            return
        
        if args[0] in ['--list', '-l', 'list']:
            list_steps()
            return
        
        # Run specified steps
        steps_to_run = args
    else:
        # Run all steps
        steps_to_run = sorted(STEPS.keys())
    
    # Validate step numbers
    invalid_steps = [s for s in steps_to_run if s not in STEPS]
    if invalid_steps:
        print(f"✗ Invalid step numbers: {', '.join(invalid_steps)}")
        print("\nUse --list to see available steps")
        sys.exit(1)
    
    # Print overall header
    print_header("NORMALIZATION PIPELINE")
    
    if clean_mode:
        print("🗑️  Clean mode: enabled")
    
    print(f"Running {len(steps_to_run)} step(s): {', '.join(steps_to_run)}")
    
    # Clean directories if requested
    if clean_mode:
        clean_output_directories(base_dir)
    
    # Track results
    results = {}
    
    # Run steps
    for step_num in steps_to_run:
        success = run_step(step_num, base_dir)
        results[step_num] = success
        
        if not success:
            print(f"\n⚠ Step {step_num} failed. Continue? [y/N] ", end='')
            response = input().strip().lower()
            if response not in ['y', 'yes']:
                print("\n✗ Normalization stopped")
                break
    
    # Print summary
    print_header("NORMALIZATION SUMMARY")
    
    successful = [s for s, r in results.items() if r]
    failed = [s for s, r in results.items() if not r]
    
    if successful:
        print("✓ Successful steps:")
        for step_num in successful:
            print(f"    Step {step_num}: {STEPS[step_num]['name']}")
        print()
    
    if failed:
        print("✗ Failed steps:")
        for step_num in failed:
            print(f"    Step {step_num}: {STEPS[step_num]['name']}")
        print()
    
    print(f"Total: {len(successful)}/{len(results)} steps completed successfully")
    print()
    
    # Exit with appropriate code
    sys.exit(0 if not failed else 1)


if __name__ == '__main__':
    main()
