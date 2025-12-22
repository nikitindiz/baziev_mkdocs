---
applyTo: '**'
---

# Замена единиц измерений в формулах

## Контекст

В процессе нормализации книги необходимо заменить текстовые единицы измерений в формулах на ссылки на соответствующие символы в графе Neo4j. Это позволяет:

-   Связать формулы с единицами измерений через отношения `CONTAINS_SYMBOL`
-   Обеспечить единообразие представления единиц измерений по всей книге
-   Упростить навигацию и анализ использования единиц измерений

## Пошаговая инструкция

### 1. Найти существующие символы единиц измерений

Перед созданием новых символов, всегда проверяй, не существуют ли они уже в базе:

```cypher
// Поиск по описанию единицы
MATCH (s:Symbol)
WHERE s.description CONTAINS 'Джоуль' OR s.description CONTAINS 'Секунда' OR
      s.description CONTAINS 'Метр' OR s.description CONTAINS 'Килограмм'
RETURN s.id, s.latex, s.value, s.description, s.units, s.type
ORDER BY s.description
```

```cypher
// Поиск по полю units
MATCH (s:Symbol)
WHERE s.units CONTAINS 'Дж' OR s.units CONTAINS 'м' OR s.units CONTAINS 'кг'
RETURN s.id, s.latex, s.value, s.description, s.units, s.type
```

### 2. Получить текущую формулу

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
RETURN f.id, f.latex, f.latex_initial
```

Обрати внимание на поле `latex_initial` - оно содержит оригинальное представление формулы с текстовыми единицами.

### 3. Проверить текущие связи формулы

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
OPTIONAL MATCH (f)-[:CONTAINS_SYMBOL]->(s:Symbol)
RETURN f.id, f.latex,
       collect({symbol_id: s.id, symbol_latex: s.latex, symbol_description: s.description}) as symbols
```

### 4. Обновить latex формулы

Замени текстовые единицы на ссылки формата `{{symbol:SYMBOL_ID}}`:

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
SET f.latex = '\\dim {{symbol:1764372946735}} = {{symbol:1764343754879}} \\cdot {{symbol:1766251789237}}'
RETURN f.id, f.latex
```

**Паттерны замены:**

| Было         | Стало                      |
| ------------ | -------------------------- |
| `\text{Дж}`  | `{{symbol:1764343754879}}` |
| `\text{с}`   | `{{symbol:1766251789237}}` |
| `\text{м}`   | `{{symbol:1764372497232}}` |
| `\text{м}^2` | `{{symbol:1764372531371}}` |
| `\text{кг}`  | `{{symbol:1764351940055}}` |
| `Н`          | `{{symbol:1764372472596}}` |

### 5. Создать связи CONTAINS_SYMBOL

После обновления latex, создай связи между формулой и всеми использованными символами:

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
MATCH (s_joule:Symbol {id: '1764343754879'})
MATCH (s_second:Symbol {id: '1766251789237'})
MATCH (s_meter:Symbol {id: '1764372497232'})
// ... остальные символы

// Удали старые связи если есть
OPTIONAL MATCH (f)-[r:CONTAINS_SYMBOL]->()
DELETE r

// Создай новые
CREATE (f)-[:CONTAINS_SYMBOL]->(s_joule)
CREATE (f)-[:CONTAINS_SYMBOL]->(s_second)
CREATE (f)-[:CONTAINS_SYMBOL]->(s_meter)
// ... для всех символов

RETURN f.id, count(*) as symbols_linked
```

### 6. Проверить результат

```cypher
MATCH (f:Formula {id: 'FORMULA_ID'})
OPTIONAL MATCH (f)-[:CONTAINS_SYMBOL]->(s:Symbol)
RETURN f.id, f.latex, f.latex_initial,
       collect({symbol_id: s.id, symbol_latex: s.latex, symbol_description: s.description}) as symbols
```

## Часто используемые единицы измерений

### Базовые единицы СИ

-   **Секунда** (с) - `1766251789237` - `\text{с}` - Время
-   **Метр** (м) - `1764372497232` - `м` - Длина
-   **Килограмм** (кг) - `1764351940055` - `\text{кг}` - Масса

### Производные единицы

-   **Джоуль** (Дж) - `1764343754879` - `\text{Дж}` - Энергия
-   **Ньютон** (Н) - `1764372472596` - `Н` - Сила
-   **Метр²** (м²) - `1764372531371` - `\text{м}^2` - Площадь

### Составные единицы

При работе со сложными единицами (например, `м/с`, `кг·м²·с⁻¹`), проверь, существуют ли они как отдельные символы, или нужно использовать композицию базовых единиц.

## Советы и лучшие практики

1. **Всегда проверяй существование символов** перед созданием новых - это предотвратит дублирование
2. **Используй OPTIONAL MATCH при удалении** старых связей - это предотвратит ошибки если связей нет
3. **Сохраняй latex_initial** - он нужен для отладки и сравнения
4. **Группируй связанные операции** - обновление latex и создание связей лучше делать в одной сессии
5. **Документируй необычные случаи** - если встречаешь нестандартную единицу, добавь комментарий

## Пример: Формула (2.6)

**Исходная формула:**

```latex
\text{dim}\,[h] = \text{Дж} \cdot \text{с} = \text{Н} \cdot \text{м} \cdot \text{с} = \frac{\text{кг} \cdot \text{м}}{\text{с}^2} \cdot \text{м} \cdot \text{с} = \frac{\text{кг} \cdot \text{м}^2}{\text{с}}
```

**После нормализации:**

```latex
\dim {{symbol:1764372946735}} = {{symbol:1764343754879}} \cdot {{symbol:1766251789237}} = {{symbol:1764372472596}} \cdot {{symbol:1764372497232}} \cdot {{symbol:1766251789237}} = \frac{{{symbol:1764351940055}} \cdot {{symbol:1764372497232}}}{{{symbol:1766251789237}}^2} \cdot {{symbol:1764372497232}} \cdot {{symbol:1766251789237}} = \frac{{{symbol:1764351940055}} \cdot {{symbol:1764372531371}}}{{{symbol:1766251789237}}}
```

**Связанные символы:** 7 (h, Дж, с, Н, м, м², кг)

## Доступ к базе данных

Используй MCP инструменты для работы с Neo4j:

-   `mcp_neo4j-aura2_read_neo4j_cypher` - для чтения данных
-   `mcp_neo4j-aura2_write_neo4j_cypher` - для записи данных
-   База: `neo4j-aura2`
-   Полные права на чтение и запись

## Типичные ошибки

1. **Забыть проверить существование символа** - создается дубликат
2. **Неправильный формат ссылки** - `{symbol:ID}` вместо `{{symbol:ID}}`
3. **Не удалить старые связи** - формула связана с устаревшими символами
4. **Забыть про экранирование** - в Cypher строки нужно правильно экранировать
5. **ORDER BY после collect** - в Neo4j нельзя сортировать по переменной после агрегации
