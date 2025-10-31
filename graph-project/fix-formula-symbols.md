# Методика рефакторинга формул-символов в Neo4j

**Задача**: Систематически найти и исправить все случаи, когда формулы в параграфах на самом деле являются одиночными символами. Отвязать такие формулы от параграфов, создать прямые связи между параграфами и символами, а в тексте заменить референсы формул на референсы символов.

**Цель**: Упростить граф знаний, убрав избыточные узлы Formula, которые дублируют Symbol, и создать единообразную систему ссылок на символы в тексте.

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
- `definition` (STRING) - определение символа
- `unit` (STRING) - единица измерения
- `confidence` (STRING) - уровень уверенности в определении (high/medium/low)
- другие поля: `symbol`, `description`, `latex_note`, `latex_corrected`, `note`, `context_note`

**Paragraph**
- `id` (STRING) - уникальный идентификатор параграфа
- `content` (STRING, indexed) - текст параграфа с референсами
- `order` (INTEGER) - порядковый номер параграфа
- `word_count` (INTEGER) - количество слов

### Связи (Relationships)

**Существующие:**
- `Formula -[:USES_SYMBOL]-> Symbol` - формула использует символ
- `Paragraph -[:CONTAINS_FORMULA]-> Formula` - параграф содержит формулу
- `Paragraph -[:NEXT]-> Paragraph` - последовательность параграфов

**Создаваемые:**
- `Paragraph -[:CONTAINS_SYMBOL]-> Symbol` - параграф содержит символ (новая связь)

## Методика работы

### Этап 1: Анализ масштаба задачи

#### 1.1 Подсчет формул-символов

```cypher
// Найти все формулы, которые являются одиночными символами
MATCH (f:Formula)-[r:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
RETURN count(DISTINCT f) as total_formula_symbols
```

#### 1.2 Проверка уникальности соответствий

```cypher
// Убедиться, что каждая формула-символ связана ровно с одним символом
MATCH (f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, count(s) as symbol_count
WHERE symbol_count > 1
RETURN count(f) as formulas_with_multiple_symbols
```

Ожидаемый результат: 0 (каждая формула должна соответствовать ровно одному символу)

#### 1.3 Анализ затронутых параграфов

```cypher
// Подсчитать количество параграфов, которые будут изменены
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
RETURN count(DISTINCT p) as affected_paragraphs,
       count(*) as total_formula_refs
```

### Этап 2: Создание связей Paragraph-Symbol

#### 2.1 Создание новых связей CONTAINS_SYMBOL

```cypher
// Для каждой формулы-символа создать связь между параграфом и символом
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
MERGE (p)-[:CONTAINS_SYMBOL]->(s)
RETURN count(*) as created_links
```

**Важно:** Используем `MERGE` вместо `CREATE`, чтобы избежать дублирования связей, если параграф уже ссылается на символ через другую формулу.

#### 2.2 Проверка созданных связей

```cypher
// Проверить, что связи созданы корректно
MATCH (p:Paragraph)-[:CONTAINS_SYMBOL]->(s:Symbol)
RETURN count(*) as total_symbol_links
```

### Этап 3: Обновление текста параграфов

**Критически важно:** Этот этап требует работы с файлами Markdown на диске, так как свойство `content` в базе данных содержит только ссылки на формулы, а сам текст хранится в файлах.

#### 3.1 Получение списка изменений для каждого параграфа

```cypher
// Для каждого параграфа получить список замен formula -> symbol
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
RETURN p.id as paragraph_id,
       p.content as paragraph_content,
       collect({
         formula_id: f.id,
         symbol_id: s.id,
         latex: f.latex
       }) as replacements
ORDER BY p.id
```

#### 3.2 Структура изменений

Для каждого параграфа нужно:
1. Определить файл, в котором он находится (по `paragraph_id`)
2. Найти все вхождения `{{formula:formula_id}}` в тексте
3. Заменить на `{{symbol:symbol_id}}`
4. Сохранить изменения в файл

**Пример замены:**
- Было: `где {{formula:db996faeccc9}} — объем шара`
- Стало: `где {{symbol:5206560a306a}} — объем шара`

#### 3.3 Скрипт для обновления файлов

Необходимо создать Python-скрипт, который:
1. Получает из Neo4j список всех замен
2. Для каждого уникального файла:
   - Читает содержимое файла
   - Выполняет все замены для параграфов из этого файла
   - Сохраняет обновленный файл
3. Логирует все изменения

**Структура данных для скрипта:**
```python
{
  "docs/chapter_название/index.md": [
    {
      "paragraph_id": "...",
      "replacements": [
        {"from": "{{formula:db996faeccc9}}", "to": "{{symbol:5206560a306a}}"},
        ...
      ]
    },
    ...
  ],
  ...
}
```

### Этап 4: Удаление связей CONTAINS_FORMULA

#### 4.1 Удаление устаревших связей

**Только после успешного обновления файлов!**

```cypher
// Удалить связи между параграфами и формулами-символами
MATCH (p:Paragraph)-[r:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
MATCH (p:Paragraph)-[r:CONTAINS_FORMULA]->(f)
DELETE r
RETURN count(r) as deleted_links
```

#### 4.2 Проверка осиротевших формул

```cypher
// Найти формулы без входящих связей (кандидаты на удаление)
MATCH (f:Formula)
WHERE NOT EXISTS { (p:Paragraph)-[:CONTAINS_FORMULA]->(f) }
AND EXISTS { (f)-[:USES_SYMBOL]->(:Symbol) }
WITH f, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
MATCH (f)-[:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
RETURN count(f) as orphaned_formulas
```

### Этап 5: Удаление узлов Formula (опционально)

**Внимание:** Удалять формулы-символы следует только если они больше нигде не используются.

#### 5.1 Удаление связей USES_SYMBOL

```cypher
// Удалить связи между формулами-символами и символами
MATCH (f:Formula)-[r:USES_SYMBOL]->(s:Symbol)
WHERE f.latex = s.latex
WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
WHERE sym_count = 1
AND NOT EXISTS { (p:Paragraph)-[:CONTAINS_FORMULA]->(f) }
MATCH (f)-[r:USES_SYMBOL]->(s)
DELETE r
RETURN count(r) as deleted_uses_symbol
```

#### 5.2 Удаление узлов Formula

```cypher
// Удалить формулы-символы, которые больше не используются
MATCH (f:Formula)
WHERE NOT EXISTS { (f)-[:USES_SYMBOL]->() }
AND NOT EXISTS { ()-[:CONTAINS_FORMULA]->(f) }
DELETE f
RETURN count(f) as deleted_formulas
```

## Валидация и проверка

### Проверка 1: Целостность данных

```cypher
// Убедиться, что нет "потерянных" референсов
MATCH (p:Paragraph)
WHERE p.content CONTAINS '{{formula:'
WITH p, [x IN split(p.content, '{{formula:') WHERE size(x) > 0 | split(x, '}}')[0]] as formula_ids
UNWIND formula_ids as formula_id
MATCH (f:Formula {id: formula_id})
OPTIONAL MATCH (p)-[:CONTAINS_FORMULA]->(f)
WHERE NOT EXISTS { (p)-[:CONTAINS_FORMULA]->(f) }
RETURN count(*) as missing_formula_links
```

### Проверка 2: Корректность замен в файлах

```cypher
// Получить список символов для валидации в файлах
MATCH (p:Paragraph)-[:CONTAINS_SYMBOL]->(s:Symbol)
RETURN p.id as paragraph_id,
       collect(s.id) as symbol_ids
ORDER BY p.id
```

Сравнить с фактическими референсами `{{symbol:id}}` в файлах.

### Проверка 3: Статистика до и после

**До рефакторинга:**
```cypher
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
RETURN count(DISTINCT p) as paragraphs_with_formulas,
       count(f) as total_formula_refs
```

**После рефакторинга:**
```cypher
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
RETURN count(DISTINCT p) as paragraphs_with_formulas,
       count(f) as total_formula_refs;

MATCH (p:Paragraph)-[:CONTAINS_SYMBOL]->(s:Symbol)
RETURN count(DISTINCT p) as paragraphs_with_symbols,
       count(s) as total_symbol_refs;
```

## Правила работы

### ❌ Запрещено

- НЕ удалять связи или узлы до обновления файлов
- НЕ выполнять операции батчами без логирования
- НЕ пропускать этапы валидации
- НЕ изменять формулы, которые используются в других контекстах

### ✅ Обязательно

- Создать резервную копию базы данных перед началом
- Создать резервную копию файлов Markdown
- Логировать все изменения
- Проверять результат каждого этапа перед переходом к следующему
- Использовать транзакции для групповых операций
- Проверять файлы на наличие корректных замен

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
```

### Определение файла по paragraph_id

`paragraph_id` имеет структуру:
```
chapter_название-главы_секция_pN
```

Где:
- `chapter_название-главы` - директория главы в `docs/`
- `секция` - название секции
- `pN` - номер параграфа

Файл находится по пути:
```
docs/chapter_название-главы/секция.md
или
docs/chapter_название-главы/index.md
```

### Пример Python-кода для замены

```python
import re
from neo4j import GraphDatabase

def get_file_path(paragraph_id):
    """Определить путь к файлу по ID параграфа"""
    # Парсинг paragraph_id
    parts = paragraph_id.split('_')
    chapter = parts[0] + '_' + parts[1]  # chapter_название
    section = '_'.join(parts[2:-1])  # секция (может содержать _)
    
    # Возможные пути
    paths = [
        f"docs/{chapter}/{section}.md",
        f"docs/{chapter}/index.md"
    ]
    
    # Проверить существование
    for path in paths:
        if os.path.exists(path):
            return path
    
    return None

def replace_in_file(file_path, replacements):
    """Выполнить замены в файле"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original = content
    for repl in replacements:
        pattern = re.escape(repl['from'])
        content = re.sub(pattern, repl['to'], content)
    
    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def process_replacements(driver):
    """Главная функция обработки"""
    # Получить все замены из Neo4j
    query = """
    MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(s:Symbol)
    WHERE f.latex = s.latex
    WITH f, s, count{(f)-[:USES_SYMBOL]->()} as sym_count
    WHERE sym_count = 1
    MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
    RETURN p.id as paragraph_id,
           collect({formula_id: f.id, symbol_id: s.id}) as replacements
    ORDER BY p.id
    """
    
    with driver.session() as session:
        result = session.run(query)
        
        # Группировать по файлам
        files = {}
        for record in result:
            para_id = record['paragraph_id']
            file_path = get_file_path(para_id)
            
            if file_path not in files:
                files[file_path] = []
            
            files[file_path].append({
                'paragraph_id': para_id,
                'replacements': [
                    {
                        'from': f"{{{{formula:{r['formula_id']}}}}}",
                        'to': f"{{{{symbol:{r['symbol_id']}}}}}"
                    }
                    for r in record['replacements']
                ]
            })
        
        # Обработать каждый файл
        for file_path, paragraphs in files.items():
            all_replacements = []
            for para in paragraphs:
                all_replacements.extend(para['replacements'])
            
            if replace_in_file(file_path, all_replacements):
                print(f"✓ Updated: {file_path}")
            else:
                print(f"○ No changes: {file_path}")
```

## Статус работы

- **Обнаружено**: 969 формул-символов
- **Затронуто параграфов**: ~5170 (требует уточнения)
- **Связей для создания**: ~969+
- **Связей для удаления**: ~969+
- **Файлов для обновления**: требует подсчета

## Важные замечания

1. **Связь CONTAINS_FORMULA** используется для всех формул, включая формулы-символы
2. **Связь CONTAINS_SYMBOL** создается новая, специально для прямых ссылок на символы
3. Параграфы могут содержать множественные ссылки на одну и ту же формулу-символ
4. После рефакторинга символы будут доступны в тексте напрямую, без промежуточного узла Formula
5. Формулы-символы могут иметь дополнительные атрибуты (например, номер формулы), которые нужно сохранить в тексте

## Следующие шаги

1. ✅ Создать документацию методики (этот файл)
2. ⬜ Создать резервные копии (база данных + файлы)
3. ⬜ Выполнить анализ масштаба (Этап 1)
4. ⬜ Создать Python-скрипт для обновления файлов
5. ⬜ Протестировать скрипт на небольшой выборке файлов
6. ⬜ Выполнить полное обновление файлов
7. ⬜ Создать связи в базе данных (Этап 2)
8. ⬜ Удалить устаревшие связи (Этап 4)
9. ⬜ Выполнить валидацию
10. ⬜ Опционально: удалить узлы Formula (Этап 5)
