# Отчет о исправлении импорта orphan таблиц

## Проблема

После импорта данных в Neo4j обнаружено:
- **14 таблиц** (из 36) не имели связей с другими узлами
- Таблицы были "orphan" - недоступны для навигации через граф
- Причина: таблицы располагались на страницах без текстовых параграфов

## Пример проблемной таблицы

**ID**: `a596885158e9`  
**Файл**: `chapter_приложение-3-периодическая-система-элементов/index.md`  
**Проблема**: В файле только таблица, нет параграфов с текстом, поэтому связь `(:Paragraph)-[:CONTAINS_TABLE]->(:Table)` не создавалась

## Анализ проблемы

### Распределение orphan таблиц

Все 14 orphan таблиц находились в главах **БЕЗ секций**:

| Глава | Таблиц |
|-------|--------|
| Приложение 1 (гиперчастотные параметры) | 6 |
| Приложение 2 (фундаментальные константы) | 5 |
| Приложение 3 (периодическая система) | 2 |
| Глава VIII (происхождение Солнечной системы) | 1 |

### Выявленные причины

1. **Нет секций в главе** - приложения не имеют подразделов
2. **Файл `index.md` без секций** - таблица находится на главной странице главы
3. **Неверная логика связывания** - код пытался найти секцию вида `chapter_X_index`, которой не существует

### Исходный код проблемы

```python
# content_linker.py, строка ~370 (СТАРАЯ ВЕРСИЯ)
section_id = f"{chapter_part}_{file_name}"

link_query = """
MATCH (s:Section {id: $section_id})  # Секция не существует!
MATCH (t:Table {id: $table_id})
MERGE (s)-[r:CONTAINS_TABLE]->(t)
"""
```

## Решение

### 1. Обновление логики связывания (content_linker.py)

**Новая стратегия**:
1. Попробовать найти и связать с секцией
2. Если секция не найдена → связать напрямую с главой

```python
# content_linker.py, строка ~356-400 (НОВАЯ ВЕРСИЯ)
# Попробовать связать с секцией
link_query = """
MATCH (s:Section {id: $section_id})
MATCH (t:Table {id: $table_id})
MERGE (s)-[r:CONTAINS_TABLE]->(t)
SET r.orphan = true
RETURN count(s) as linked  # Проверяем, была ли найдена секция
"""

result = self.conn.execute_query(link_query, {
    "section_id": section_id,
    "table_id": table_id
})

if result and result[0]['linked'] > 0:
    # Секция найдена, таблица связана
    linked_count += 1
else:
    # Секция не найдена → связать с главой
    link_query = """
    MATCH (c:Chapter {id: $chapter_id})
    MATCH (t:Table {id: $table_id})
    MERGE (c)-[r:CONTAINS_TABLE]->(t)
    SET r.orphan = true
    """
    
    self.conn.execute_query(link_query, {
        "chapter_id": chapter_id,
        "table_id": table_id
    })
    
    linked_count += 1
```

### 2. То же самое для иллюстраций

Аналогичные изменения применены к `link_orphan_illustrations()` (строки ~430-480).

### 3. Обновление скрипта проверки (check_table_links.py)

Теперь проверяет связи не только от `Paragraph`, но и от `Chapter` и `Section`:

```python
# Было:
OPTIONAL MATCH (p:Paragraph)-[:CONTAINS_TABLE]->(t)

# Стало:
OPTIONAL MATCH (n)-[:CONTAINS_TABLE]->(t)  # Любой узел
WITH t, count(n) as link_count, collect(labels(n)[0]) as link_types
```

## Результаты

### До исправления
```
Всего таблиц: 36
Со связями: 22
Без связей: 14
```

### После исправления
```
Всего таблиц: 36
Со связями: 36
Без связей: 0

Распределение по типам связей:
  Paragraph: 22  (61%)
  Chapter: 14    (39%)
```

### Полная статистика графа

```
📊 УЗЛЫ:              17,154
  - Book:                  1
  - Chapter:              15
  - Section:              43
  - Paragraph:         6,921
  - Formula:           9,815
  - Symbol:              206
  - Illustration:         69
  - Table:                36
  - Literature:           48

🔗 СВЯЗИ:             23,756
  - CONTAINS_TABLE:       36  ✅ (100% покрытие)
  - CONTAINS_ILLUSTRATION: 69  ✅ (100% покрытие)
  - CONTAINS_FORMULA:  5,730  (~58% покрытие)
  - CITES:                32
```

## Проверка

### Запуск импорта
```bash
cd /Users/electrino/work/vibed/baziev_mkdocs/graph-project
source venv/bin/activate
python main.py import link-orphans
```

### Проверка статистики
```bash
python graph_stats.py
```

### Cypher запросы для проверки

**Найти все таблицы, связанные с главами**:
```cypher
MATCH (c:Chapter)-[r:CONTAINS_TABLE]->(t:Table)
RETURN c.id as chapter_id, c.title as title, 
       count(t) as tables, collect(t.id) as table_ids
ORDER BY c.id
```

**Проверить конкретную таблицу**:
```cypher
MATCH (t:Table {id: 'a596885158e9'})
OPTIONAL MATCH (n)-[r]->(t)
RETURN t.id, t.source, type(r) as rel_type, 
       labels(n)[0] as from_type, n.id as from_id
```

## Изменённые файлы

1. **src/importers/content_linker.py**
   - Метод `link_orphan_artifacts_to_sections()` (строки 348-511)
   - Добавлена логика fallback к главе, если секция не найдена

2. **check_table_links.py**
   - Обновлён запрос статистики для учёта связей от любых узлов
   - Добавлен вывод распределения по типам связей

3. **graph_stats.py** (НОВЫЙ)
   - Полная статистика графа знаний
   - Детализация по всем типам узлов и связей

4. **README.md**
   - Обновлена секция "Статистика" с реальными данными
   - Добавлена ссылка на `graph_stats.py`

## Коммит

```bash
git add src/importers/content_linker.py \
        check_table_links.py \
        graph_stats.py \
        README.md

git commit -m "Fix orphan table linking: fallback to Chapter if Section not found

- Modified link_orphan_artifacts_to_sections() to try Section first, then Chapter
- Applied same logic to both tables and illustrations
- Updated check_table_links.py to count links from any node type
- Added graph_stats.py with full knowledge graph statistics
- Updated README.md with actual import statistics

Result: 36/36 tables linked (100% coverage)
  - 22 tables linked to Paragraphs (61%)
  - 14 tables linked to Chapters (39%)
"
```

## Уроки

1. **Не все артефакты находятся в тексте параграфов** - некоторые страницы содержат только таблицы/рисунки
2. **Гибкая логика связывания** - нужно предусмотреть fallback механизмы
3. **Проверка существования узлов** - `RETURN count(s)` помогает проверить успешность MATCH
4. **Статистика критична** - без детальной статистики трудно выявить проблемы покрытия

## След. шаги

1. ✅ Все таблицы связаны
2. ✅ Все иллюстрации связаны
3. ⏳ Улучшить покрытие формул (сейчас ~58%)
4. ⏳ Связать orphan литературу
5. ⏳ Добавить концептуальные связи (DEFINES, MENTIONS)
