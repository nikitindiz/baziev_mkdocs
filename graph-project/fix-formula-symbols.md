# Методика рефакторинга формул-символов в Neo4j

**Задача**: Систематически проверить и обработать все формулы-символы (формулы, содержащие только один символ). Для каждой формулы-символа:
1. Проверить, что определение символа соответствует контексту использования
2. Отвязать формулу от параграфа
3. Создать прямую связь между параграфом и символом
4. Заменить референс формулы на референс символа в markdown-файле

**Цель**: Упростить граф знаний, убрав избыточные узлы Formula, которые дублируют Symbol, и создать единообразную систему ссылок на символы в тексте. Одновременно проверить корректность определений символов в контексте их использования.

**Для AI-агента**: Этот документ является инструкцией для пошаговой работы. Обрабатывай формулы-символы по одной, помечай обработанные, продолжай с того места, где остановился в прошлый раз.

## Проблема

В текущей структуре базы данных:
- **969 формул** являются одиночными символами (формула содержит ровно один символ, и `formula.latex = symbol.latex`)
- Параграфы ссылаются на эти формулы через `CONTAINS_FORMULA`
- В тексте параграфов используются референсы вида `{{formula:id}}`
- Прямых связей `CONTAINS_SYMBOL` между параграфами и символами не существует

**Пример текущего состояния:**
```
Paragraph: "где {{formula:db996faeccc9}} — объем шара"
   |
   ↓ CONTAINS_FORMULA
Formula {id: "db996faeccc9", latex: "V"}
   |
   ↓ USES_SYMBOL
Symbol {id: "5206560a306a", latex: "V", definition: "объем"}
```

**Желаемое состояние (простой символ):**
```
Paragraph: "где {{symbol:5206560a306a}} — объем шара"
   |
   ↓ CONTAINS_SYMBOL
Symbol {id: "5206560a306a", latex: "V", definition: "объем"}
```

**Пример с индексированным символом:**

**Текущее состояние:**
```
Paragraph: "А каково значение {{formula:e8de5d5eecaa}}, следующее из классической теории?"
   |
   ↓ CONTAINS_FORMULA
Formula {id: "e8de5d5eecaa", latex: "E_0"}
   |
   ├─ USES_SYMBOL → Symbol {id: "13a248d66e72", latex: "E_{0}", definition: "начальная энергия"}
   └─ USES_SYMBOL → Symbol {id: "3a3ea00cfc35", latex: "E", definition: "энергия (общее обозначение)"}
```

**Желаемое состояние (индексированный символ):**
```
Paragraph: "А каково значение {{symbol:13a248d66e72}}, следующее из классической теории?"
   |
   ↓ CONTAINS_SYMBOL
Symbol {id: "13a248d66e72", latex: "E_{0}", definition: "начальная энергия"}
   |
   ↓ USES_SYMBOL
Symbol {id: "3a3ea00cfc35", latex: "E", definition: "энергия (общее обозначение)"}
```

## Структура Neo4j базы данных

### Узлы (Nodes)

**Formula**
- `id` (STRING, unique, indexed) - уникальный идентификатор формулы
- `latex` (STRING, indexed) - LaTeX представление формулы
- `symbols` (LIST) - список символов в формуле
- `type`, `source`, `metadata`, `wrapper_html` (STRING) - метаданные

**Symbol**
- `id` (STRING, unique, indexed) - уникальный идентификатор символа
- `latex` (STRING, indexed) - LaTeX представление символа
- `latex_corrected` (STRING) - исправленное LaTeX представление (если `latex` содержит ошибку)
- `definition` (STRING) - определение символа
- `unit` (STRING) - единица измерения
- `confidence` (STRING) - уровень уверенности в определении (high/medium/low)
- другие поля: `symbol`, `description`, `latex_note`, `note`, `context_note`

**Paragraph**
- `id` (STRING) - уникальный идентификатор параграфа
- `content` (STRING, indexed) - текст параграфа с референсами
- `order` (INTEGER) - порядковый номер параграфа
- `word_count` (INTEGER) - количество слов
- `formula_symbols_processed` (BOOLEAN) - флаг обработки формул-символов в параграфе

### Связи (Relationships)

**Существующие:**
- `Formula -[:USES_SYMBOL]-> Symbol` - формула использует символ
- `Paragraph -[:CONTAINS_FORMULA]-> Formula` - параграф содержит формулу
- `Paragraph -[:NEXT]-> Paragraph` - последовательность параграфов

**Создаваемые:**
- `Paragraph -[:CONTAINS_SYMBOL]-> Symbol` - параграф содержит символ (новая связь)

## Методика работы для AI-агента

### Принцип работы

**ВАЖНО:** Работай ПОСЛЕДОВАТЕЛЬНО, по одному параграфу за раз:
1. Получи следующий необработанный параграф
2. Найди все формулы в этом параграфе
3. Для каждой формулы определи, является ли она формулой-символом
4. Для каждой формулы-символа:
   - Проверь контекст использования символа
   - Создай связь `CONTAINS_SYMBOL`
   - Замени референс в файле
5. Когда все формулы-символы в параграфе обработаны - помечай параграф флагом `formula_symbols_processed = true`
6. При следующем запуске продолжай со следующего необработанного параграфа

### Этап 0: Статус выполнения

#### 0.1 Проверка прогресса

```cypher
// Узнать общий статус обработки
MATCH (p:Paragraph)
WHERE p.formula_symbols_processed IS NULL OR p.formula_symbols_processed = false
WITH count(p) as remaining_paragraphs
MATCH (p:Paragraph)
WITH count(p) as total_paragraphs
MATCH (p:Paragraph)
WHERE p.formula_symbols_processed = true
WITH count(p) as processed_paragraphs, total_paragraphs, remaining_paragraphs
RETURN total_paragraphs, processed_paragraphs, remaining_paragraphs
```

**Ожидаемый результат при первом запуске:**
- `total_paragraphs`: 291 (уникальных параграфов с формулами-символами)
- `processed_paragraphs`: 0
- `remaining_paragraphs`: 291

### Этап 1: Получение следующего параграфа для обработки

#### Этап 1.1: Получить следующий необработанный параграф

```cypher
// Найти первый необработанный параграф
MATCH (p:Paragraph)
WHERE p.formula_symbols_processed IS NULL OR p.formula_symbols_processed = false
RETURN p.id as paragraph_id,
       p.content as paragraph_content,
       p.order as paragraph_order
ORDER BY p.id
LIMIT 1
```

**Для агента:** Если запрос вернул пустой результат - все параграфы обработаны ✅

#### Этап 1.2: Получить все формулы из параграфа

```cypher
// Получить все формулы параграфа
MATCH (p:Paragraph {id: $paragraph_id})-[:CONTAINS_FORMULA]->(f:Formula)
RETURN f.id as formula_id
ORDER BY f.id
```

**Для агента:** Если результат пустой - параграф не содержит формул, переходи к Этапу 4.2

#### Этап 1.3: Определить формулы-символы в параграфе

**ВАЖНОЕ УТОЧНЕНИЕ:** Формула считается формулой-символом в трех случаях:
1. **Простой символ**: формула содержит один символ, и `formula.latex = symbol.latex` (или `symbol.latex_corrected`)
2. **Индексированный символ (связанный)**: формула связана с несколькими символами, но один из них является "основным" (его latex совпадает с formula.latex), а остальные - "вложенные" (используются в индексах)
3. **Индексированный символ (несвязанный)**: формула имеет индекс (например `m_i`, `\rho_i`), связана с базовым символом (например `m`, `\rho`), но в базе НЕТ символа с полным latex. В этом случае нужно найти или создать индексированный символ.

**Примеры:**
- `V` → один символ `V` (объем) - простой случай
- `E_0` → основной символ `E_{0}` (начальная энергия) + вложенный символ `E` (энергия) - индексированный связанный случай
- `m_i` → формула связана с базовым символом `m` (масса), но символа `m_i` в базе нет - индексированный несвязанный случай (требует создания)
- `A^{в}` → основной символ `A^{в}` амплитуда колебания молекулы воды в нормальных условиях (A - амплитуда с индексом в, где в = вода)
- `\frac{E}{mc^2}` → формула из нескольких символов - НЕ формула-символ

```cypher
// Найти все формулы-символы в параграфе
MATCH (p:Paragraph {id: $paragraph_id})-[:CONTAINS_FORMULA]->(f:Formula)
MATCH (f)-[:USES_SYMBOL]->(s:Symbol)
WITH f, collect(s) as matching_symbols
WHERE size(matching_symbols) = 1
WITH f, matching_symbols[0] as s
RETURN f.id as formula_id,
       s.id as symbol_id,
       s.definition as symbol_definition,
       s.unit as symbol_unit,
       s.confidence as symbol_confidence,
       [] as nested_symbols  // пустой список для совместимости
ORDER BY f.id

UNION

// Найти все индексированные формулы-символы в параграфе
MATCH (p:Paragraph {id: $paragraph_id})-[:CONTAINS_FORMULA]->(f:Formula)
MATCH (f)-[:USES_SYMBOL]->(s:Symbol)
WITH f, s, collect{(f)-[:USES_SYMBOL]->(other:Symbol) WHERE other.id <> s.id | other} as nested
WHERE size(nested) > 0
RETURN f.id as formula_id,
       s.id as symbol_id,
       s.definition as symbol_definition,
       s.unit as symbol_unit,
       s.confidence as symbol_confidence,
       nested as nested_symbols
ORDER BY f.id
```

**Для агента:** 
- Если результат пустой - переходи к Этапу 1.4 для проверки несвязанных индексированных символов
- Если `nested_symbols` не пустой - это индексированный символ, нужно создать связи между символами (см. Этап 3.1.1)

#### Этап 1.4: Обработка несвязанных индексированных формул-символов

**Выполняй ТОЛЬКО если Этап 1.3 не нашел формулы-символы!**

Некоторые формулы с индексами (например `m_i`, `\rho_i`, `\delta_{i1}`, `A^{п}`) могут быть связаны только с базовыми символами (`m`, `\rho`, `\delta`, `A`), но не иметь соответствующего индексированного символа в базе.

### 1.4.1: Поиск несвязанных индексированных формул

```cypher
// Найти формулы с индексами, которые связаны только с базовыми символами
MATCH (p:Paragraph {id: $paragraph_id})-[:CONTAINS_FORMULA]->(f:Formula)
WHERE f.latex =~ '.*[_^].*'  // содержит _ или ^ (индекс или степень)
MATCH (f)-[:USES_SYMBOL]->(s:Symbol)
WITH f, collect(s) as symbols
WHERE size(symbols) > 0
  AND NOT any(s IN symbols WHERE s.latex = f.latex OR s.latex_corrected = f.latex)
RETURN f.id as formula_id,
       f.latex as formula_latex,
       [s IN symbols | {id: s.id, latex: s.latex, definition: s.definition}] as related_symbols
ORDER BY f.id
```

### 1.4.2: Обработка каждой найденной формулы

Для каждой найденной формулы с индексом:

#### Шаг 1: Получить контекст (используй Этап 2.1)

#### Шаг 2: Проанализировать формулу
- Разбери структуру: базовый символ + индекс(ы)
- Пример: `m_i` = базовый `m` + индекс `i`
- Пример: `\delta_{i1}` = базовый `\delta` + индексы `i` и `1`

#### Шаг 3: Определить значение из контекста
- Прочитай текущий параграф и соседние
- Определи, что обозначает индексированный символ
- Пример: "где m_i — масса осциллятора" → определение = "масса осциллятора"

#### Шаг 4: Поискать похожий символ в базе

```cypher
// Поиск похожих индексированных символов
MATCH (s:Symbol)
WHERE s.latex STARTS WITH 'БАЗОВЫЙ_СИМВОЛ'  // например 'm'
  AND s.latex CONTAINS '_'  // или '^'
RETURN s.id as symbol_id,
       s.latex as symbol_latex,
       s.definition as symbol_definition,
       s.unit as symbol_unit
ORDER BY s.latex
```

#### Шаг 5а: Если похожий символ найден И определение совпадает

- Используй найденный символ
- Создай связь `Formula -[:USES_SYMBOL]-> Symbol`
- Продолжи обработку как в Этапе 3

#### Шаг 5б: Если похожего символа НЕТ или определение отличается

- Создай новый Symbol (см. Этап 1.4.3)
- Создай связь `Formula -[:USES_SYMBOL]-> Symbol`
- Продолжи обработку как в Этапе 3

### 1.4.3: Создание нового индексированного символа

**Выполняй только после анализа контекста и поиска похожих символов!**

```cypher
// Создать новый индексированный символ
CREATE (s:Symbol {
  id: randomUUID(),
  latex: 'LATEX_ИНДЕКСИРОВАННОГО_СИМВОЛА',  // например 'm_{i}'
  definition: 'ОПРЕДЕЛЕНИЕ_ИЗ_КОНТЕКСТА',
  unit: 'ЕДИНИЦА_ИЗМЕРЕНИЯ',  // если применимо, иначе null
  confidence: 'high',  // или 'medium' если есть сомнения
  symbol: 'LATEX_БЕЗ_ОБРАТНЫХ_СЛЭШЕЙ'  // например 'm_i'
})
RETURN s.id as new_symbol_id, s.latex as symbol_latex
```

**Затем создай связи:**

```cypher
// Связать формулу с новым символом
MATCH (f:Formula {id: 'FORMULA_ID'})
MATCH (s:Symbol {id: 'NEW_SYMBOL_ID'})
MERGE (f)-[:USES_SYMBOL]->(s)
RETURN f.latex, s.latex
```

```cypher
// Связать новый символ с базовым символом (если есть)
MATCH (s_indexed:Symbol {id: 'NEW_SYMBOL_ID'})
MATCH (s_base:Symbol {id: 'BASE_SYMBOL_ID'})  // базовый символ (например 'm')
MERGE (s_indexed)-[:USES_SYMBOL]->(s_base)
RETURN s_indexed.latex, s_base.latex
```

**Повтори для каждого вложенного символа (индексы):**

```cypher
// Связать с символом индекса (если есть)
MATCH (s_indexed:Symbol {id: 'NEW_SYMBOL_ID'})
MATCH (s_index:Symbol {id: 'INDEX_SYMBOL_ID'})  // символ индекса (например 'i')
MERGE (s_indexed)-[:USES_SYMBOL]->(s_index)
RETURN s_indexed.latex, s_index.latex
```

### 1.4.4: Логирование

**Пример лога:**

```
[2025-10-31 10:05] - Formula m_i (d110052db303) has no matching indexed symbol
[2025-10-31 10:05]   └─ Related symbols: m (6f8f57715090, "масса"), i (865c0c0b4ab0, "индекс")
[2025-10-31 10:05]   └─ Context: "где m_i — масса осциллятора"
[2025-10-31 10:05]   └─ Created new Symbol: m_{i} (NEW_ID, "масса осциллятора")
[2025-10-31 10:05]   └─ Linked: m_{i} -[:USES_SYMBOL]-> m
[2025-10-31 10:05]   └─ Linked: m_{i} -[:USES_SYMBOL]-> i
[2025-10-31 10:05]   └─ Linked: Formula m_i -[:USES_SYMBOL]-> m_{i}
```

### 1.4.5: Продолжение обработки

**Для агента:** После обработки всех несвязанных индексированных формул:
- Если формул-символов в параграфе всё еще нет - переходи к Этапу 4.2 (пометить параграф обработанным)
- Если формулы-символы были найдены/созданы - продолжай с Этапа 2 (обработка формул-символов)

## Обновленные примечания

### Типичные проблемы - ДОПОЛНЕНО

**Проблема**: `formula.latex ≠ symbol.latex`
**Решение**: 
1. Проверь `symbol.latex_corrected`
2. Если формула индексированная (содержит `_` или `^`) и связана только с базовыми символами - используй Этап 1.4 для создания нового индексированного символа

**Проблема**: Формула `m_i` связана только с символом `m`, но не с `m_i`
**Решение**: Это несвязанный индексированный символ - используй Этап 1.4

**Проблема**: Не уверен, нужно ли создавать новый символ или искать существующий
**Решение**: Всегда сначала ищи похожие символы в базе. Создавай новый только если не нашел или определение отличается.

### Этап 2: Обработка формул-символов в параграфе

#### 2.1 Получить контекст параграфа для проверки символов

```cypher
// Получить текст текущего и соседних параграфов (для проверки контекста всех символов)
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
OPTIONAL MATCH (prev:Paragraph)-[:NEXT]->(p)
OPTIONAL MATCH (p)-[:NEXT]->(next:Paragraph)
RETURN p.id as current_id,
       p.content as current_content,
       prev.id as prev_id,
       prev.content as prev_content,
       next.id as next_id,
       next.content as next_content
```

**Для агента:** 
- Прочитай текст текущего и соседних параграфов для понимания контекста
- Учти, что многие параграфы содержат только референсы `{{formula:id}}` - в таких случаях используй соседние параграфы

#### 2.2 Для каждой формулы-символа: проверка определения

**Для каждого символа из результата Этапа 1.3:**

1. **Проверить контекст использования:**
   - Соответствует ли `symbol.definition` тексту параграфа?
   - Если параграф содержит только референсы - проверь соседние параграфы

2. **Посмотреть другие использования символа (опционально):**
```cypher
// Найти другие формулы с этим символом
MATCH (f:Formula)-[:USES_SYMBOL]->(s:Symbol {id: 'SYMBOL_ID'})
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
RETURN f.id as formula_id,
       f.latex as formula_latex,
       p.id as paragraph_id,
       substring(p.content, 0, 300) as context_snippet
LIMIT 5
```

#### 2.3 Обновление определения символа (если нужно)

**Для каждого символа:**

- **Если определение КОРРЕКТНО:** ничего не делай, переходи к следующему символу
- **Если определение НЕКОРРЕКТНО или отсутствует:** обнови его:

```cypher
MATCH (s:Symbol {id: 'SYMBOL_ID'})
SET s.definition = 'НОВОЕ_ОПРЕДЕЛЕНИЕ',
    s.confidence = 'high'  // или 'medium', 'low'
RETURN s
```

- **Если `formula.latex ≠ symbol.latex`:** проверь `symbol.latex_corrected`

### Этап 3: Создание связей и замена в базе данных

#### 3.1 Создание связей CONTAINS_SYMBOL для всех формул-символов параграфа

**Для каждой формулы-символа из списка (Этап 1.3):**

```cypher
// Создать связь между параграфом и основным символом
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
MATCH (s:Symbol {id: 'SYMBOL_ID'})
MERGE (p)-[:CONTAINS_SYMBOL]->(s)
RETURN p.id, s.id
```

**Важно:** Используем `MERGE`, чтобы избежать дублирования связей.

#### 3.1.1 Создание связей между символами для индексированных формул-символов

**ТОЛЬКО если `nested_symbols` не пустой (из результата Этапа 1.3):**

Для индексированных символов (например, `E_0` = основной символ `E_{0}` + вложенный `E`) нужно создать связи `USES_SYMBOL` между основным и вложенными символами.

```cypher
// Создать связь между основным символом и каждым вложенным
MATCH (s_main:Symbol {id: 'MAIN_SYMBOL_ID'})
MATCH (s_nested:Symbol {id: 'NESTED_SYMBOL_ID'})
MERGE (s_main)-[:USES_SYMBOL]->(s_nested)
RETURN s_main.latex as main_symbol, s_nested.latex as nested_symbol
```

**Для агента:**
- Выполни этот запрос для КАЖДОГО вложенного символа из списка `nested_symbols`
- Это сохраняет информацию о том, что индексированный символ содержит другие символы
- Пример: `E_{0} -[:USES_SYMBOL]-> E` означает, что символ `E_0` использует символ `E` в своей записи

#### 3.2 Замена референсов формул на символы в содержимом параграфа

**Для каждой формулы-символа из списка (Этап 1.3):**

```cypher
// Обновить content параграфа - заменить {{formula:ID}} на {{symbol:ID}}
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
SET p.content = replace(p.content, '{{formula:FORMULA_ID}}', '{{symbol:SYMBOL_ID}}')
RETURN p.content as updated_content
```

**ВАЖНО:** 
- Замена происходит непосредственно в свойстве `p.content` в базе данных
- Markdown файлы НЕ изменяются - все изменения только в Neo4j
- Функция `replace()` заменит все вхождения `{{formula:FORMULA_ID}}` в тексте
- Если формула имеет номер `{{formula:ID:(1.1)}}`, замена сработает только для точного совпадения

### Этап 4: Завершение обработки параграфа

#### 4.1 Удаление связей CONTAINS_FORMULA для всех обработанных формул-символов

**Только после успешной замены ВСЕХ формул-символов в `p.content`!**

**Для каждой формулы-символа из списка (Этап 1.3):**

```cypher
// Удалить связь между параграфом и формулой-символом
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})-[r:CONTAINS_FORMULA]->(f:Formula {id: 'FORMULA_ID'})
DELETE r
RETURN count(r) as deleted_link
```

#### 4.2 Пометить параграф как обработанный

```cypher
// Установить флаг обработки для параграфа
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
SET p.formula_symbols_processed = true
RETURN p.id, p.formula_symbols_processed
```

**Для агента:** После этого вернись к Этапу 1.1 и получи следующий необработанный параграф.

### Этап 5: Финальная очистка (после обработки ВСЕХ параграфов)

**Выполняй ТОЛЬКО когда все параграфы обработаны!**

#### 5.1 Проверка готовности к очистке

```cypher
// Убедиться, что все параграфы обработаны
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE (f.latex = s.latex OR f.latex = s.latex_corrected)
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count, p
WHERE sym_count = 1
AND (p.formula_symbols_processed IS NULL OR p.formula_symbols_processed = false)
RETURN count(p) as unprocessed_paragraphs
```

Если результат `0` - можно продолжать очистку.

#### 5.2 Удаление осиротевших формул-символов

```cypher
// Найти и удалить формулы-символы без связей с параграфами
MATCH (f:Formula)-[r:USES_SYMBOL]->(s:Symbol)
WHERE (f.latex = s.latex OR f.latex = s.latex_corrected)
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
AND NOT EXISTS { (:Paragraph)-[:CONTAINS_FORMULA]->(f) }
// Удалить связь USES_SYMBOL
DELETE r
// Удалить узел Formula
WITH f
DELETE f
RETURN count(f) as deleted_formulas
```

## Валидация и проверка (на каждом шаге)

### Проверка перед обработкой параграфа

```cypher
// Проверить, что формула действительно содержит только один символ
MATCH (f:Formula {id: 'FORMULA_ID'})
MATCH (f)-[:USES_SYMBOL]->(s)
RETURN count(s) as symbol_count,
       collect(s.id) as symbols
```

Ожидаемо: `symbol_count = 1`

### Проверка после замены в базе данных

**Для агента:**
1. Прочитай обновленное `p.content` из базы
2. Убедись, что `{{formula:FORMULA_ID}}` больше нет в тексте
3. Убедись, что `{{symbol:SYMBOL_ID}}` присутствует в нужном месте
4. Если были номера формул - убедись, что они сохранены

**Пример проверки:**
```cypher
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
RETURN p.content
```

### Итоговая статистика

```cypher
// Общая статистика обработки
MATCH (p:Paragraph)
WHERE p.formula_symbols_processed = true
WITH count(p) as processed
MATCH (p:Paragraph)-[:CONTAINS_SYMBOL]->(s:Symbol)
WITH processed, count(DISTINCT p) as with_symbols, count(*) as total_symbol_refs
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
WITH processed, with_symbols, total_symbol_refs,
     count(DISTINCT p) as with_formulas, count(*) as total_formula_refs
RETURN processed as processed_paragraphs,
       with_symbols as paragraphs_with_direct_symbols,
       total_symbol_refs as total_symbol_references,
       with_formulas as paragraphs_with_formulas,
       total_formula_refs as total_formula_references
```

## Правила работы для AI-агента

### ❌ ЗАПРЕЩЕНО

- НЕ обрабатывать несколько параграфов одновременно - только ПО ОДНОМУ
- НЕ удалять связи или узлы до замены ВСЕХ формул-символов в `p.content`
- НЕ пропускать проверку контекста символов
- НЕ пропускать пометку параграфа как обработанного
- НЕ изменять формулы, которые являются сложными выражениями (не формулами-символами)
- НЕ выполнять Этап 5 (финальную очистку) до завершения всех параграфов
- **НЕ изменять markdown файлы в директории `docs/` - только база данных!**

### ✅ ОБЯЗАТЕЛЬНО

- Работать СТРОГО ПОСЛЕДОВАТЕЛЬНО: один параграф -> все его формулы-символы -> следующий параграф
- Обрабатывать ВСЕ формулы-символы в параграфе перед переходом к следующему
- ВСЕГДА проверять контекст символов в текущем и соседних параграфах
- ВСЕГДА помечать обработанный параграф флагом `formula_symbols_processed = true`
- Проверять `symbol.latex_corrected` если `formula.latex ≠ symbol.latex`
- Сохранять номера формул при замене (например, `(1.1)`)
- Выполнять все замены в `p.content` через Cypher запросы
- **ВСЕ операции выполнять ТОЛЬКО в базе данных Neo4j**
- Логировать каждый шаг:
  - Какой параграф обработан
  - Сколько формул-символов в нем найдено
  - Какие формулы заменены на какие символы
  - Что изменено в `p.content`
  - При следующем запуске начинать с первого необработанного параграфа

### 🔄 Алгоритм работы

```
НАЧАЛО СЕССИИ:
1. Запросить статус (Этап 0.1)
2. Если remaining_paragraphs = 0 -> ЗАВЕРШИТЬ или перейти к Этапу 5

ОСНОВНОЙ ЦИКЛ (повторять до исчерпания параграфов):
3. Получить следующий необработанный параграф и вывести его содержимое в чат (Этап 1.1)
4. Если результат пустой -> ЗАВЕРШИТЬ или перейти к Этапу 5
5. Получить все формулы параграфа (Этап 1.2)
6. Определить формулы-символы (Этап 1.3)
7. Если формул-символов нет -> пометить параграф обработанным (Этап 4.2) и вернуться к шагу 3
8. Получить контекст параграфа (Этап 2.1)
9. ДЛЯ КАЖДОЙ формулы-символа в параграфе:
   9.1. Проверить определение символа (Этап 2.2-2.3)
   9.2. При необходимости - обновить определение
   9.3. Создать связь CONTAINS_SYMBOL (Этап 3.1)
   9.4. ЕСЛИ это индексированный символ - создать связи USES_SYMBOL между символами (Этап 3.1.1)
   9.5. Заменить референс в p.content (Этап 3.2)
10. Проверить корректность замен в p.content
11. ДЛЯ КАЖДОЙ формулы-символа: удалить связь CONTAINS_FORMULA (Этап 4.1)
12. Пометить параграф как обработанный и вывести содержимое обработанного параграфа в чат (Этап 4.2)
13. Вернуться к шагу 3

ЗАВЕРШЕНИЕ (когда все параграфы обработаны):
16. Выполнить финальную очистку (Этап 5)
17. Показать итоговую статистику
```

## Технические детали

### Формат референсов в p.content

**Формула:**
```
{{formula:db996faeccc9}}
{{formula:db996faeccc9:(1.1)}}  // с номером формулы
```

**Символ:**
```
{{symbol:5206560a306a}}
{{symbol:5206560a306a:(1.1)}}  // с номером
```

### Важно о работе с данными

**ВСЕ изменения происходят ТОЛЬКО в базе данных Neo4j:**
- Свойство `Paragraph.content` обновляется через Cypher запросы
- Markdown файлы в директории `docs/` НЕ изменяются
- Связи создаются и удаляются в графе
- Флаги обработки устанавливаются на узлах Paragraph

## Начальная статистика

- **Обнаружено формул-символов**: 969
- **Параграфов для обработки**: проверить через Этап 0.1
- **Текущий прогресс**: проверить через Этап 0.1

### Команда для быстрого старта

```cypher
// Получить первый необработанный параграф
MATCH (p:Paragraph)
WHERE p.formula_symbols_processed IS NULL OR p.formula_symbols_processed = false
RETURN p.id as paragraph_id,
       p.content as paragraph_content
ORDER BY p.id
LIMIT 1
```

**Для агента:** Начни работу с выполнения этого запроса!

## Важные замечания для AI-агента

### Особенности данных

1. **latex vs latex_corrected**: Иногда правильное LaTeX представление находится в `symbol.latex_corrected`, а не в `symbol.latex`. При сравнении `formula.latex` с символом проверяй ОБА поля.

1.1. **Индексированные символы (связанные)**: Формула может быть связана с несколькими символами, если один из них является "основным" (совпадает с formula.latex), а другие - вложенные. Пример: формула `E_0` связана с символом `E_{0}` (основной) и `E` (вложенный). В таких случаях:
   - Создай связь `Paragraph -[:CONTAINS_SYMBOL]-> Symbol(основной)`
   - Создай связи `Symbol(основной) -[:USES_SYMBOL]-> Symbol(вложенный)` для каждого вложенного
   - Замени `{{formula:id}}` на `{{symbol:id_основного}}`

1.2. **Индексированные символы (несвязанные)**: Формулы с индексами (например `m_i`, `\rho_i`, `\delta_{i1}`) могут быть связаны только с базовыми символами, но не иметь соответствующего индексированного символа в базе. При обработке таких случаев (Этап 1.4):
   - Изучи контекст использования
   - Поищи похожие индексированные символы в базе
   - Если не нашел - создай новый Symbol с правильным latex и определением из контекста
   - Создай связи между новым символом, формулой и базовыми символами
   - Продолжи обработку как обычную формулу-символ

2. **Контекст символа**: Многие параграфы содержат ТОЛЬКО референсы формул без текста. В таких случаях:
   - Читай предыдущий параграф (`prev.content`)
   - Читай следующий параграф (`next.content`)
   - Ищи объяснение символа в соседних параграфах

3. **Множественные вхождения**: Один параграф может ссылаться на одну и ту же формулу-символ несколько раз. Замени ВСЕ вхождения `{{formula:ID}}` на `{{symbol:ID}}`.

4. **Номера формул**: Сохраняй номера при замене:
   - `{{formula:abc123:(1.1)}}` -> `{{symbol:xyz789:(1.1)}}`

5. **Определение символа**: Если `symbol.definition` = "физическая величина" или другое общее определение - это признак, что определение нужно уточнить на основе контекста.

### Типичные проблемы

**Проблема**: Параграф содержит только `{{formula:id}}`
**Решение**: Читай соседние параграфы через связь `NEXT`

**Проблема**: `formula.latex ≠ symbol.latex`
**Решение**: 
1. Проверь `symbol.latex_corrected`
2. Если формула индексированная (содержит `_` или `^`) и связана только с базовыми символами - используй Этап 1.4 для создания нового индексированного символа

**Проблема**: Формула `m_i` связана только с символом `m`, но не с `m_i`
**Решение**: Это несвязанный индексированный символ - используй Этап 1.4

**Проблема**: Не уверен, нужно ли создавать новый символ или искать существующий
**Решение**: Всегда сначала ищи похожие символы в базе. Создавай новый только если не нашел или определение отличается

**Проблема**: `symbol.definition` слишком общее
**Решение**: Изучи контекст использования и обнови определение

**Проблема**: Символ используется в разных значениях
**Решение**: Это сложный случай - возможно нужно создать отдельные Symbol узлы для каждого значения (см. #file:fix-symbols.md п.8)

## КРИТИЧЕСКИ ВАЖНОЕ УСЛОВИЕ: Эквивалентность записи символов

### Правило соответствия символов

ПРИ СВЯЗЫВАНИИ параграфа с символом (создание `CONTAINS_SYMBOL`) **ОБЯЗАТЕЛЬНО** проверяй:

**Символ, с которым мы связываем параграф, должен быть эквивалентен по записи символу в формуле (formula.latex) или его скорректированной версии (symbol.latex_corrected).**

### Что считается эквивалентным:

1. **Точное совпадение**: 
   - `formula.latex = symbol.latex` (например, `V` = `V`)
   - `formula.latex = symbol.latex_corrected` (если latex был исправлен)

2. **ИСКЛЮЧЕНИЕ - фигурные скобки в индексах**: Символы с индексами считаются эквивалентными независимо от наличия фигурных скобок:
   - `A_i` ≡ `A_{i}` (эквивалентны)
   - `E_0` ≡ `E_{0}` (эквивалентны)
   - `\delta_{i1}` ≡ `\delta_i1` (эквивалентны, но это плохая запись - лучше добавить скобки)
   - `m_i` ≡ `m_{i}` (эквивалентны)

### Примеры применения:

**✅ ПРАВИЛЬНО:**
```
Formula {latex: "E_0"} → Symbol {latex: "E_{0}"} 
// Можно связать: E_0 эквивалентно E_{0}

Formula {latex: "V"} → Symbol {latex: "V"}
// Можно связать: точное совпадение

Formula {latex: "m_i"} → Symbol {latex: "m_{i}"}
// Можно связать: m_i эквивалентно m_{i}
```

**❌ НЕПРАВИЛЬНО:**
```
Formula {latex: "m_i"} → Symbol {latex: "m"}
// НЕЛЬЗЯ связать: m_i НЕ эквивалентно m
// Это разные символы! m - базовый, m_i - индексированный

Formula {latex: "E_0"} → Symbol {latex: "E"}
// НЕЛЬЗЯ связать: E_0 НЕ эквивалентно E
// Нужен символ E_{0} или E_0

Formula {latex: "\\rho_i"} → Symbol {latex: "\\rho"}
// НЕЛЬЗЯ связать: ρ_i НЕ эквивалентно ρ
```

### Алгоритм проверки эквивалентности:

```python
def is_equivalent(formula_latex, symbol_latex, symbol_latex_corrected=None):
    """
    Проверка эквивалентности записи символов
    """
    # Нормализация: убираем фигурные скобки из индексов для сравнения
    def normalize(latex):
        import re
        # Заменяем _{X} на _X и ^{X} на ^X для одиночных символов
        latex = re.sub(r'_\{([^}])\}', r'_\1', latex)
        latex = re.sub(r'\^\{([^}])\}', r'^\1', latex)
        return latex
    
    formula_norm = normalize(formula_latex)
    symbol_norm = normalize(symbol_latex)
    
    # Проверяем точное совпадение после нормализации
    if formula_norm == symbol_norm:
        return True
    
    # Проверяем с latex_corrected если он есть
    if symbol_latex_corrected:
        corrected_norm = normalize(symbol_latex_corrected)
        if formula_norm == corrected_norm:
            return True
    
    return False
```

### Что делать если эквивалентного символа нет:

**Если формула `m_i` связана только с символом `m` (не эквивалентны!):**

1. **ЭТО НЕСВЯЗАННЫЙ ИНДЕКСИРОВАННЫЙ СЛУЧАЙ** → используй Этап 1.4
2. Изучи контекст использования формулы
3. Поищи в базе символ с latex `m_i` или `m_{i}`
4. Если не нашел:
   - Создай новый Symbol с `latex: "m_{i}"` (с фигурными скобками)
   - Определи значение из контекста
   - Создай связи: Formula→Symbol(m_i), Symbol(m_i)→Symbol(m), Symbol(m_i)→Symbol(i)
5. Теперь можно связать параграф с эквивалентным символом `m_{i}`

### Проверка при обработке:

**ПЕРЕД созданием связи `CONTAINS_SYMBOL` (Этап 3.1) ВСЕГДА проверяй:**

```cypher
// Проверить эквивалентность символа
MATCH (f:Formula {id: 'FORMULA_ID'})
MATCH (s:Symbol {id: 'SYMBOL_ID'})
WITH f, s,
     // Нормализация для сравнения
     replace(replace(f.latex, '_{', '_'), '^{', '^') as f_norm,
     replace(replace(s.latex, '_{', '_'), '^{', '^') as s_norm,
     replace(replace(coalesce(s.latex_corrected, s.latex), '_{', '_'), '^{', '^') as s_corr_norm
RETURN f.latex as formula_latex,
       s.latex as symbol_latex,
       s.latex_corrected as symbol_latex_corrected,
       f_norm = s_norm OR f_norm = s_corr_norm as is_equivalent
```

Если `is_equivalent = false` → **НЕ СОЗДАВАЙ связь!** Используй Этап 1.4 для обработки.

## Прогресс выполнения

### Трекинг для AI-агента

**При КАЖДОМ запуске:**
1. Запроси статус через Этап 0.1
2. Запиши в лог:
   - Дата/время сессии
   - Количество обработанных параграфов в этой сессии
   - Количество оставшихся параграфов
   - Список обработанных paragraph_id

**Формат лога:**
```
[2025-10-31 10:00] Session started
[2025-10-31 10:00] Status: 150/5000 paragraphs processed, 4850 remaining

[2025-10-31 10:01] Processing paragraph: chapter_глава-i_1-секция_p5
[2025-10-31 10:01] - Found 3 formula-symbols in paragraph
[2025-10-31 10:01] - Formula db996faeccc9 (V) -> Symbol 5206560a306a (объем) - SIMPLE, definition OK
[2025-10-31 10:01] - Formula ce2d9fa1df5e (ε) -> Symbol f8b1c5a729a0 (Энергия) - SIMPLE, definition OK
[2025-10-31 10:01] - Formula c5703f02a0e3 (r) -> Symbol 4b43b0aee356 (радиус) - SIMPLE, definition OK
[2025-10-31 10:01] - p.content updated: 3 replacements in database ✓
[2025-10-31 10:01] - All formula-symbols processed, paragraph marked as processed ✓

[2025-10-31 10:02] Processing paragraph: chapter_глава-i-система-новейших-фундаментальных-открытий_1-гиперчастотная-механика-или-механика-микромира_p19
[2025-10-31 10:02] - Found 1 formula-symbol in paragraph
[2025-10-31 10:02] - Formula e8de5d5eecaa (E_0) -> Symbol 13a248d66e72 (E_{0}) - INDEXED
[2025-10-31 10:02]   └─ Nested symbols: [E (3a3ea00cfc35)]
[2025-10-31 10:02]   └─ Created Symbol-to-Symbol link: E_{0} -[:USES_SYMBOL]-> E ✓
[2025-10-31 10:02] - p.content updated: {{formula:e8de5d5eecaa}} -> {{symbol:13a248d66e72}} ✓
[2025-10-31 10:02] - Paragraph marked as processed ✓

[2025-10-31 10:03] Processing paragraph: chapter_глава-i_1-секция_p7
[2025-10-31 10:03] - Found 0 formula-symbols in paragraph
[2025-10-31 10:03] - Paragraph marked as processed ✓

...
[2025-10-31 10:30] Session ended: 25 paragraphs processed
[2025-10-31 10:30] Status: 175/5000 paragraphs processed, 4825 remaining
```

### Чеклист завершения

- [ ] Все параграфы обработаны (`remaining_paragraphs = 0`)
- [ ] Все `p.content` обновлены (проверено выборочно)
- [ ] Определения символов уточнены где необходимо
- [ ] Связи `CONTAINS_SYMBOL` созданы
- [ ] Связи `CONTAINS_FORMULA` для формул-символов удалены
- [ ] Финальная очистка выполнена (Этап 5)
- [ ] Итоговая статистика показана
