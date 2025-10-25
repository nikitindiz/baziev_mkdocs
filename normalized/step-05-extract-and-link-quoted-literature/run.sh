#!/bin/bash
# Quick run script for Step 05
# Executes parse-refs.py with proper error handling

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                    STEP 05: EXTRACT LITERATURE REFERENCES                  ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $PYTHON_VERSION"
echo ""

# Check input directory
echo "Checking input directory..."
if [ ! -d "../step-04-parse-missed-db-keys-and-src/result" ]; then
    echo "✗ Error: Step 04 result directory not found!"
    echo "  Please run Step 04 first."
    exit 1
fi
echo "✓ Step 04 result directory found"
echo ""

# Check bibliography file
echo "Checking bibliography file..."
BIB_FILE="../../docs/chapter_список-цитированной-литературы/index.md"
if [ ! -f "$BIB_FILE" ]; then
    echo "✗ Error: Bibliography file not found!"
    echo "  Expected: $BIB_FILE"
    exit 1
fi
echo "✓ Bibliography file found"
echo ""

# Run the script
echo "Running parse-refs.py..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 parse-refs.py
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "✓ Step 05 completed successfully!"
    echo ""
    echo "Next steps:"
    echo "  1. Review extraction_stats.json"
    echo "  2. Validate literature files: ls -l ../../literature/"
    echo "  3. Check result directory: ls -l result/"
    echo ""
else
    echo ""
    echo "✗ Step 05 failed with exit code: $EXIT_CODE"
    exit $EXIT_CODE
fi
