#!/bin/bash

# Тест API для редактирования формул
# Использование: ./test-formula-api.sh

BASE_URL="http://localhost:3000"

echo "🧪 Testing Formula API"
echo "====================="
echo ""

# Получаем первую формулу из базы для теста
FORMULA_ID="71300187ea8c"  # ID из примера выше

echo "1️⃣  GET /api/formulas/${FORMULA_ID}"
echo "-----------------------------------"
curl -s "${BASE_URL}/api/formulas/${FORMULA_ID}" | jq '.'
echo ""
echo ""

echo "2️⃣  PATCH /api/formulas/${FORMULA_ID} - Update symbol info"
echo "-----------------------------------------------------------"
curl -s -X PATCH "${BASE_URL}/api/formulas/${FORMULA_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "is_symbol": true,
    "symbol_definition": "Реакция диссоциации кислорода",
    "symbol_parse_confidence": "high"
  }' | jq '.'
echo ""
echo ""

echo "3️⃣  GET /api/formulas/${FORMULA_ID} - Verify update"
echo "-----------------------------------------------------"
curl -s "${BASE_URL}/api/formulas/${FORMULA_ID}" | jq '.'
echo ""
echo ""

echo "4️⃣  PATCH /api/formulas/${FORMULA_ID} - Revert symbol info"
echo "-----------------------------------------------------------"
curl -s -X PATCH "${BASE_URL}/api/formulas/${FORMULA_ID}" \
  -H "Content-Type: application/json" \
  -d '{
    "is_symbol": false
  }' | jq '.'
echo ""
echo ""

echo "✅ Tests completed!"
