#!/bin/bash
cd /Users/electrino/work/vibed/baziev_mkdocs/normalized/step-02-extract-all-tables

echo "Testing new pattern..."
python3 test_new_pattern.py

echo ""
echo "Running extraction..."
rm -rf tables result
python3 extract-tables.py

echo ""
echo "Results:"
echo "Table files: $(ls -1 tables/*.json 2>/dev/null | wc -l)"
echo "Types:"
ls tables/*.json 2>/dev/null | xargs -I {} sh -c 'cat {} | python3 -c "import sys, json; print(json.load(sys.stdin)[\"type\"])"' | sort | uniq -c
