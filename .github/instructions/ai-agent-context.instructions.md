---
applyTo: '**'
---

# Контекст для AI агента: Работа с графом книги "Основы единой теории физики"

## Что это за проект

Книга Джабраила Базиева "Основы единой теории физики" была оцифрована и преобразована в граф знаний в Neo4j. Граф содержит структурированные данные о параграфах, формулах и символах книги.

## Доступ к базе данных Neo4j

### MCP инструменты

-   **`mcp_neo4j-aura2_read_neo4j_cypher`** - чтение данных (Cypher-запросы)
-   **`mcp_neo4j-aura2_write_neo4j_cypher`** - запись/изменение данных
-   **`mcp_neo4j-aura2_get_neo4j_schema`** - получение схемы базы

### База данных

-   Название: `neo4j-aura2`
-   Доступ: полные права на чтение и запись

## Структура графа

### Узлы (Nodes)

**Paragraph** - параграфы книги

-   `id` - уникальный идентификатор параграфа
-   `content` - текст параграфа с ссылками на формулы/символы

**Formula** - математические формулы

-   `id` - уникальный идентификатор
-   `latex` - нормализованное LaTeX представление (со ссылками `{{symbol:ID}}`)
-   `latex_initial` - оригинальное LaTeX представление
-   `type` - тип формулы: `'inline'` или `'display'`
-   `number` - номер формулы (если есть), например "(2.7)"

**Symbol** - символы (переменные, константы, единицы измерений)

-   `id` - уникальный идентификатор
-   `latex` - LaTeX представление символа (например `r_i`, `h`, `\text{м}`)
-   `description` - текстовое описание на русском
-   `type` - тип символа: `'variable'`, `'constant'`, `'unit'` или `null`
-   `units` - единицы измерения (для переменных/констант)
-   `value` - числовое значение (для констант)

### Связи (Relationships)

-   `(Paragraph)-[:CONTAINS_FORMULA]->(Formula)` - параграф содержит формулу
-   `(Formula)-[:CONTAINS_SYMBOL]->(Symbol)` - формула использует символ

## Что искать в базе

### Поиск параграфов с формулами

```cypher
// Найти параграф и его формулы
MATCH (p:Paragraph {id: 'PARAGRAPH_ID'})
OPTIONAL MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
RETURN p.id, p.content, collect(f) as formulas
```

### Поиск формул по главам

```cypher
// Формулы в конкретной главе
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
WHERE p.id STARTS WITH 'chapter_глава-i-'
RETURN p.id, f.id, f.latex, f.type, f.number
ORDER BY p.id
```

### Поиск символов

```cypher
// Поиск по описанию
MATCH (s:Symbol)
WHERE s.description CONTAINS 'скорость'
RETURN s.id, s.latex, s.description, s.type

// Поиск по типу
MATCH (s:Symbol {type: 'unit'})
RETURN s.id, s.latex, s.description

// Поиск единиц измерений
MATCH (s:Symbol)
WHERE s.units CONTAINS 'м' OR s.description CONTAINS 'Метр'
RETURN s.id, s.latex, s.units, s.description
```

### Анализ связей формулы

```cypher
// Какие символы использует формула
MATCH (f:Formula {id: 'FORMULA_ID'})
OPTIONAL MATCH (f)-[:CONTAINS_SYMBOL]->(s:Symbol)
RETURN f.latex, collect({
  symbol_id: s.id,
  symbol_latex: s.latex,
  symbol_type: s.type,
  symbol_description: s.description
}) as symbols
```

### Поиск необработанных формул

```cypher
// Формулы без символов
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
WHERE NOT (f)-[:CONTAINS_SYMBOL]->(:Symbol)
RETURN p.id, f.id, f.latex_initial, f.type
ORDER BY p.id
LIMIT 10
```

### Поиск соседних параграфов

```cypher
// Предыдущие параграфы (для контекста)
MATCH (p:Paragraph {id: 'CURRENT_PARAGRAPH_ID'})
WITH substring(p.id, 0, size(p.id) - 4) as prefix
MATCH (prev:Paragraph)
WHERE prev.id < 'CURRENT_PARAGRAPH_ID'
  AND prev.id STARTS WITH prefix
RETURN prev.id, prev.content
ORDER BY prev.id DESC
LIMIT 3

// Следующие параграфы
MATCH (p:Paragraph {id: 'CURRENT_PARAGRAPH_ID'})
WITH substring(p.id, 0, size(p.id) - 3) as prefix
MATCH (next:Paragraph)
WHERE next.id > 'CURRENT_PARAGRAPH_ID'
  AND next.id STARTS WITH prefix
RETURN next.id, next.content
ORDER BY next.id
LIMIT 3
```

## Типичные ID единиц измерений

| Единица   | ID              | LaTeX        | Описание |
| --------- | --------------- | ------------ | -------- |
| Секунда   | `1766251789237` | `\text{с}`   | Время    |
| Метр      | `1764372497232` | `м`          | Длина    |
| Метр²     | `1764372531371` | `\text{м}^2` | Площадь  |
| Килограмм | `1764351940055` | `\text{кг}`  | Масса    |
| Джоуль    | `1764343754879` | `\text{Дж}`  | Энергия  |
| Ньютон    | `1764372472596` | `Н`          | Сила     |

_Примечание: всегда проверяй актуальность этих ID через поиск в базе_

## Формат ссылок

### В тексте параграфа

-   На формулу: `{{formula:FORMULA_ID}}`
-   На символ: `{{symbol:SYMBOL_ID}}`

### В LaTeX формулы

-   На символ: `{{symbol:SYMBOL_ID}}`

## Проверка прогресса работы

```cypher
// Статистика по главе
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
WHERE p.id STARTS WITH 'chapter_глава-i-'
OPTIONAL MATCH (f)-[:CONTAINS_SYMBOL]->(s:Symbol)
WITH f, count(s) as symbol_count
RETURN
  count(*) as total_formulas,
  sum(CASE WHEN symbol_count > 0 THEN 1 ELSE 0 END) as processed,
  sum(CASE WHEN symbol_count = 0 THEN 1 ELSE 0 END) as remaining
```

## Важные паттерны

### Определения символов в тексте

Ищи в соседних параграфах:

-   "где `r_i` — средний радиус орбиты"
-   "`v_{si}` есть секториальная скорость"
-   "постоянная Планка `h`"
-   "`n_i` — среднее угловое движение"

### Проверка существования перед созданием

Всегда проверяй наличие символа:

```cypher
MATCH (s:Symbol)
WHERE s.latex = 'r_i' OR s.description CONTAINS 'радиус орбиты'
RETURN s.id, s.latex, s.description
```

### Создание нового символа

```cypher
CREATE (s:Symbol {
  id: toString(timestamp()),
  latex: 'v_{si}',
  description: 'Секториальная скорость i-ой планеты',
  type: 'variable',
  units: 'м² · с⁻¹'
})
RETURN s
```

## Полезные операции

### Обновление формулы

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
SET f.latex = '{{symbol:ID1}} = {{symbol:ID2}}^2 \\cdot {{symbol:ID3}}'
RETURN f
```

### Создание связей

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
MATCH (s:Symbol {id: 'SYMBOL_ID'})
CREATE (f)-[:CONTAINS_SYMBOL]->(s)
```

### Удаление связей

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})-[r:CONTAINS_SYMBOL]->()
DELETE r
```

### Осиротить формулу

```cypher
MATCH (p:Paragraph)-[r:CONTAINS_FORMULA]->(f:Formula {id: 'FORMULA_ID'})
DELETE r
```

## Справочная информация

-   **Подробные инструкции**: см. файлы в папке `.github/instructions/`
-   **Fixes и заметки**: папка `fixes-required/`
-   **Граф проекта**: папка `graph-project/`
-   **Нормализованные данные**: папка `normalized/`
-   **Пользовательский редактор книги**: папка `book-editor/`
