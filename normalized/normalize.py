#!/usr/bin/env python3
"""
Master Normalization Script for Baziev Physics Book
Runs all extraction steps in sequence:
1. Extract formulas
2. Extract tables
3. Extract illustrations

This script orchestrates the entire normalization pipeline.
"""

import sys
import subprocess
from pathlib import Path
from typing import List, Tuple


class NormalizationPipeline:
    """Manages the complete normalization pipeline"""
    
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.steps = [
            {
                'name': 'Step 1: Extract Formulas',
                'script': self.base_dir / 'step-01-extract-all-formulas' / 'extract-formulas.py',
                'description': 'Extracting inline and display LaTeX formulas'
            },
            {
                'name': 'Step 2: Extract Tables',
                'script': self.base_dir / 'step-02-extract-all-tables' / 'extract-tables.py',
                'description': 'Extracting Markdown and HTML tables'
            },
            {
                'name': 'Step 3: Extract Illustrations',
                'script': self.base_dir / 'step-03-extract-all-illustrations' / 'extract-illustrations.py',
                'description': 'Extracting SVG illustrations and captions'
            }
        ]
    
    def validate_scripts(self) -> List[str]:
        """Validate that all required scripts exist"""
        missing = []
        for step in self.steps:
            if not step['script'].exists():
                missing.append(str(step['script']))
        return missing
    
    def run_step(self, step: dict) -> Tuple[bool, str]:
        """Run a single normalization step"""
        script_path = step['script']
        
        print(f"\n{'=' * 80}")
        print(f"Running: {step['name']}")
        print(f"{'=' * 80}")
        print(f"Description: {step['description']}")
        print(f"Script: {script_path.name}")
        print()
        
        try:
            # Run the script using Python
            result = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=False,
                text=True,
                cwd=script_path.parent
            )
            
            if result.returncode != 0:
                return False, f"Script exited with code {result.returncode}"
            
            print(f"\n✓ {step['name']} completed successfully")
            return True, ""
            
        except subprocess.CalledProcessError as e:
            return False, f"Script failed: {e}"
        except Exception as e:
            return False, f"Unexpected error: {e}"
    
    def run_all(self) -> int:
        """Run all normalization steps in sequence"""
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 20 + "BAZIEV BOOK NORMALIZATION PIPELINE" + " " * 24 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print("This script will run the following steps:")
        for i, step in enumerate(self.steps, 1):
            print(f"  {i}. {step['name']}")
            print(f"     → {step['description']}")
        print()
        
        # Validate scripts
        print("Validating scripts...")
        missing = self.validate_scripts()
        if missing:
            print("✗ Error: Missing required scripts:")
            for script in missing:
                print(f"  - {script}")
            return 1
        print("✓ All scripts found")
        
        # Run each step
        failed_steps = []
        for i, step in enumerate(self.steps, 1):
            success, error = self.run_step(step)
            
            if not success:
                print(f"\n✗ {step['name']} FAILED")
                print(f"Error: {error}")
                failed_steps.append(step['name'])
                
                # Ask if user wants to continue
                print("\nDo you want to continue with the next step? (y/n): ", end="")
                try:
                    response = input().strip().lower()
                    if response != 'y':
                        print("\nPipeline stopped by user.")
                        break
                except KeyboardInterrupt:
                    print("\n\nPipeline interrupted by user.")
                    return 1
        
        # Summary
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print("║" + " " * 30 + "PIPELINE SUMMARY" + " " * 32 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        
        total_steps = len(self.steps)
        successful_steps = total_steps - len(failed_steps)
        
        print(f"Total steps:       {total_steps}")
        print(f"Successful steps:  {successful_steps}")
        print(f"Failed steps:      {len(failed_steps)}")
        
        if failed_steps:
            print("\nFailed steps:")
            for step in failed_steps:
                print(f"  ✗ {step}")
            print()
            print("Please check the error messages above and fix the issues.")
            return 1
        else:
            print()
            print("✓ All normalization steps completed successfully!")
            print()
            print("Output locations:")
            print(f"  - Final normalized content: {self.base_dir / 'step-03-extract-all-illustrations' / 'result'}")
            print(f"  - Extracted formulas:       {self.base_dir / 'formulas'}")
            print(f"  - Extracted tables:         {self.base_dir / 'tables'}")
            print(f"  - Extracted illustrations:  {self.base_dir / 'illustrations'}")
            print()
            return 0


def main():
    """Main entry point"""
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    
    # Create and run pipeline
    pipeline = NormalizationPipeline(str(script_dir))
    exit_code = pipeline.run_all()
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
