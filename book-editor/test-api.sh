#!/bin/bash

# Тестирование Paragraphs API

BASE_URL="http://localhost:3000/api/paragraphs"

echo "=== Testing Paragraphs API ==="
echo ""

echo "1. Testing GET /api/paragraphs (first page, limit 5)"
echo "Command: curl \"${BASE_URL}?limit=5\""
echo ""
curl -s "${BASE_URL}?limit=5" | jq '.'
echo ""
echo "---"
echo ""

echo "2. Testing GET /api/paragraphs (with cursor)"
echo "Getting first page to extract cursor..."
RESPONSE=$(curl -s "${BASE_URL}?limit=3")
CURSOR=$(echo $RESPONSE | jq -r '.pagination.cursor')
echo "Cursor: $CURSOR"
echo ""
if [ "$CURSOR" != "null" ]; then
  echo "Command: curl \"${BASE_URL}?limit=3&cursor=${CURSOR}\""
  echo ""
  curl -s "${BASE_URL}?limit=3&cursor=${CURSOR}" | jq '.'
  echo ""
fi
echo "---"
echo ""

echo "3. Testing GET /api/paragraphs/:id"
echo "Getting first paragraph ID..."
FIRST_ID=$(curl -s "${BASE_URL}?limit=1" | jq -r '.data[0].id')
echo "ID: $FIRST_ID"
echo ""
echo "Command: curl \"${BASE_URL}/${FIRST_ID}\""
echo ""
curl -s "${BASE_URL}/${FIRST_ID}" | jq '.'
echo ""
echo "---"
echo ""

echo "4. Testing pagination metadata"
echo "Command: curl \"${BASE_URL}?limit=10\""
echo ""
curl -s "${BASE_URL}?limit=10" | jq '{
  total: .pagination.total,
  hasMore: .pagination.hasMore,
  cursor: .pagination.cursor,
  loaded: (.data | length)
}'
echo ""
echo "---"
echo ""

echo "5. Testing invalid limit"
echo "Command: curl \"${BASE_URL}?limit=200\""
echo ""
curl -s "${BASE_URL}?limit=200" | jq '.'
echo ""
echo "---"
echo ""

echo "6. Testing not found paragraph"
echo "Command: curl \"${BASE_URL}/nonexistent-id\""
echo ""
curl -s "${BASE_URL}/nonexistent-id" | jq '.'
echo ""

echo "=== Tests completed ==="
