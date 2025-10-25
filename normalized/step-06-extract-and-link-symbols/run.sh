#!/bin/bash

# Step 06: Extract Symbols and Link to Formulas
# Quick execution script

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║  Step 06: Extract Symbols and Link to Formulas                ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed"
    exit 1
fi

# Run the extraction script
echo -e "${GREEN}Running extraction script...${NC}"
echo ""

python3 extract-symbols.py

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Step 06 completed successfully!                              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Show output summary
echo "Output locations:"
echo "  • Symbols:      ../symbols/symbol_*.json"
echo "  • Formulas:     ../formulas/formula_*.json (updated)"
echo "  • Statistics:   extraction_stats.json"
echo ""
echo "To view statistics:"
echo "  cat extraction_stats.json | jq"
echo ""
