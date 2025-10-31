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

**Желаемое состояние:**
```
Paragraph: "где {{symbol:5206560a306a}} — объем шара"
   |
   ↓ CONTAINS_SYMBOL
Symbol {id: "5206560a306a", latex: "V", definition: "объем"}
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
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex OR f.latex = s.latex_corrected
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
WITH DISTINCT p
WITH count(p) as total,
     sum(CASE WHEN p.formula_symbols_processed = true THEN 1 ELSE 0 END) as processed
RETURN total as total_paragraphs,
       processed as processed_paragraphs,
       total - processed as remaining_paragraphs
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
RETURN f.id as formula_id,
       f.latex as formula_latex
ORDER BY f.id
```

**Для агента:** Если результат пустой - параграф не содержит формул, переходи к Этапу 4.2

#### Этап 1.3: Определить формулы-символы в параграфе

```cypher
// Найти все формулы-символы в параграфе
MATCH (p:Paragraph {id: $paragraph_id})-[:CONTAINS_FORMULA]->(f:Formula)
MATCH (f)-[:USES_SYMBOL]->(s:Symbol)
WHERE (f.latex = s.latex OR f.latex = s.latex_corrected)
WITH f, collect(s) as matching_symbols
WHERE size(matching_symbols) = 1
WITH f, matching_symbols[0] as s
RETURN f.id as formula_id,
       f.latex as formula_latex,
       s.id as symbol_id,
       s.latex as symbol_latex,
       s.latex_corrected as symbol_latex_corrected,
       s.definition as symbol_definition,
       s.unit as symbol_unit,
       s.confidence as symbol_confidence
ORDER BY f.id
```

**Для агента:** Если результат пустой - формулы-символов нет, переходи к Этапу 4.2

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

### Этап 3: Создание связей и замена в файле

#### 3.1 Создание связей CONTAINS_SYMBOL для всех формул-символов параграфа

**Для каждой формулы-символа из списка (Этап 1.3):**

```cypher
// Создать связь между параграфом и символом
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
MATCH (s:Symbol {id: 'SYMBOL_ID'})
MERGE (p)-[:CONTAINS_SYMBOL]->(s)
RETURN p.id, s.id
```

**Важно:** Используем `MERGE`, чтобы избежать дублирования связей.

#### 3.2 Определение файла для замены

**Структура `paragraph_id`:**
```
chapter_название-главы_секция_pN
```

Примеры:
- `chapter_глава-i-система-новейших-фундаментальных-открытий_1-гиперчастотная-механика-или-механика-микромира_p1`
- Файл: `docs/chapter_глава-i-система-новейших-фундаментальных-открытий/1-гиперчастотная-механика-или-механика-микромира.md`

#### 3.3 Замена всех референсов формул-символов в файле

**Для агента:**
1. Определи путь к файлу из `paragraph_id`
2. Используй `read_file` для чтения файла
3. **Для КАЖДОЙ формулы-символа из списка (Этап 1.3):**
   - Найди все вхождения `{{formula:FORMULA_ID}}` или `{{formula:FORMULA_ID:(номер)}}`
   - Замени на `{{symbol:SYMBOL_ID}}` или `{{symbol:SYMBOL_ID:(номер)}}`
4. Сохрани файл используя `replace_string_in_file`

**ВАЖНО:** Обрабатывай все замены в одном файле за один раз!

**Примеры замен:**
- `{{formula:db996faeccc9}}` → `{{symbol:5206560a306a}}`
- `{{formula:9fc0cb23f7c1:(1.1)}}` → `{{symbol:xyz789:(1.1)}}`

**Алгоритм определения файла:**
```python
paragraph_id = "chapter_глава-i_1-секция_p1"
parts = paragraph_id.split('_')
# parts = ["chapter", "глава-i", "1-секция", "p1"]

chapter = f"{parts[0]}_{parts[1]}"  # "chapter_глава-i"
section = '_'.join(parts[2:-1])      # "1-секция"

# Возможные пути:
# 1. docs/chapter_глава-i/1-секция.md
# 2. docs/chapter_глава-i/index.md (если секция совпадает с главой)
```

### Этап 4: Завершение обработки параграфа

#### 4.1 Удаление связей CONTAINS_FORMULA для всех обработанных формул-символов

**Только после успешной замены ВСЕХ формул-символов в файле!**

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
       collect(s.latex) as symbols
```

Ожидаемо: `symbol_count = 1`

### Проверка после замены в файле

**Для агента:**
1. Прочитай обновленный файл
2. Убедись, что `{{formula:FORMULA_ID}}` больше нет в тексте
3. Убедись, что `{{symbol:SYMBOL_ID}}` присутствует в нужном месте
4. Если были номера формул - убедись, что они сохранены

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
- НЕ удалять связи или узлы до замены ВСЕХ формул-символов в файле
- НЕ пропускать проверку контекста символов
- НЕ пропускать пометку параграфа как обработанного
- НЕ изменять формулы, которые содержат более одного символа
- НЕ выполнять Этап 5 (финальную очистку) до завершения всех параграфов

### ✅ ОБЯЗАТЕЛЬНО

- Работать СТРОГО ПОСЛЕДОВАТЕЛЬНО: один параграф -> все его формулы-символы -> следующий параграф
- Обрабатывать ВСЕ формулы-символы в параграфе перед переходом к следующему
- ВСЕГДА проверять контекст символов в текущем и соседних параграфах
- ВСЕГДА помечать обработанный параграф флагом `formula_symbols_processed = true`
- Проверять `symbol.latex_corrected` если `formula.latex ≠ symbol.latex`
- Сохранять номера формул при замене (например, `(1.1)`)
- Выполнять все замены в файле за один раз (не по одной формуле)
- Логировать каждый шаг:
  - Какой параграф обработан
  - Сколько формул-символов в нем найдено
  - Какие формулы заменены на какие символы
  - Что изменено в файле
- При следующем запуске начинать с первого необработанного параграфа

### 🔄 Алгоритм работы

```
НАЧАЛО СЕССИИ:
1. Запросить статус (Этап 0.1)
2. Если remaining_paragraphs = 0 -> ЗАВЕРШИТЬ или перейти к Этапу 5

ОСНОВНОЙ ЦИКЛ (повторять до исчерпания параграфов):
3. Получить следующий необработанный параграф (Этап 1.1)
4. Если результат пустой -> ЗАВЕРШИТЬ или перейти к Этапу 5
5. Получить все формулы параграфа (Этап 1.2)
6. Определить формулы-символы (Этап 1.3)
7. Если формул-символов нет -> пометить параграф обработанным (Этап 4.2) и вернуться к шагу 3
8. Получить контекст параграфа (Этап 2.1)
9. ДЛЯ КАЖДОЙ формулы-символа в параграфе:
   9.1. Проверить определение символа (Этап 2.2-2.3)
   9.2. При необходимости - обновить определение
   9.3. Создать связь CONTAINS_SYMBOL (Этап 3.1)
10. Определить файл параграфа (Этап 3.2)
11. Заменить ВСЕ референсы формул-символов в файле за раз (Этап 3.3)
12. Проверить корректность замен
13. ДЛЯ КАЖДОЙ формулы-символа: удалить связь CONTAINS_FORMULA (Этап 4.1)
14. Пометить параграф как обработанный (Этап 4.2)
15. Вернуться к шагу 3

ЗАВЕРШЕНИЕ (когда все параграфы обработаны):
16. Выполнить финальную очистку (Этап 5)
17. Показать итоговую статистику
```

## Технические детали

### Формат референсов

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

### Определение файла по paragraph_id

`paragraph_id` имеет структуру:
```
chapter_название-главы_секция_pN
```

Примеры:
- `chapter_глава-i-система-новейших-фундаментальных-открытий_1-гиперчастотная-механика_p1`
- Файл: `docs/chapter_глава-i-система-новейших-фундаментальных-открытий/1-гиперчастотная-механика.md`

Если секция совпадает с названием главы, файл может быть `index.md` в директории главы.

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
**Решение**: Проверь `symbol.latex_corrected`

**Проблема**: `symbol.definition` слишком общее
**Решение**: Изучи контекст использования и обнови определение

**Проблема**: Символ используется в разных значениях
**Решение**: Это сложный случай - возможно нужно создать отдельные Symbol узлы для каждого значения (см. #file:fix-symbols.md п.8)

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
[2025-10-31 10:01] - Formula db996faeccc9 (V) -> Symbol 5206560a306a (объем) - definition OK
[2025-10-31 10:01] - Formula ce2d9fa1df5e (ε) -> Symbol f8b1c5a729a0 (Энергия) - definition OK
[2025-10-31 10:01] - Formula c5703f02a0e3 (r) -> Symbol 4b43b0aee356 (радиус) - definition OK
[2025-10-31 10:01] - File updated: docs/chapter_глава-i/1-секция.md (3 replacements)
[2025-10-31 10:01] - All formula-symbols processed, paragraph marked as processed ✓

[2025-10-31 10:02] Processing paragraph: chapter_глава-i_1-секция_p7
[2025-10-31 10:02] - Found 0 formula-symbols in paragraph
[2025-10-31 10:02] - Paragraph marked as processed ✓

...
[2025-10-31 10:30] Session ended: 25 paragraphs processed
[2025-10-31 10:30] Status: 175/5000 paragraphs processed, 4825 remaining
```

### Чеклист завершения

- [ ] Все параграфы обработаны (`remaining_paragraphs = 0`)
- [ ] Все файлы обновлены (проверено выборочно)
- [ ] Определения символов уточнены где необходимо
- [ ] Связи `CONTAINS_SYMBOL` созданы
- [ ] Связи `CONTAINS_FORMULA` для формул-символов удалены
- [ ] Финальная очистка выполнена (Этап 5)
- [ ] Итоговая статистика показана
