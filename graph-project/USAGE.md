# Руководство по использованию

## Быстрый старт

### 1. Установка Neo4j

**MacOS:**
```bash
brew install neo4j
neo4j start
```

**Docker:**
```bash
docker run -d \
  --name neo4j-baziev \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  -v $PWD/neo4j-data:/data \
  neo4j:latest
```

### 2. Настройка проекта

```bash
cd graph-project
./setup.sh
```

### 3. Конфигурация

Отредактируйте `config/config.yml`:

```yaml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "ваш_пароль"
  database: "baziev"

paths:
  # Важно! Используем документы со ссылками на сущности
  docs: "../normalized/step-05-extract-and-link-quoted-literature/result"
  formulas: "../normalized/formulas"
  symbols: "../normalized/symbols"
  # и т.д.
```

**Примечание:** Путь `docs` должен указывать на `normalized/step-05-extract-and-link-quoted-literature/result`, так как именно там находятся markdown файлы со ссылками на сущности в формате `{{formula:hash}}`, `{{symbol:hash}}` и т.д.

### 4. Импорт данных

```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Импортировать все данные
python main.py import all

# Или поэтапно:
python main.py import structure
python main.py import formulas
python main.py import symbols
python main.py import illustrations
python main.py import tables
python main.py import literature
python main.py import paragraphs
python main.py import link-content
```

## Работа с графом

### Запросы

```bash
# Показать статистику
python main.py stats

# Статистика по главам
python main.py query chapter-stats

# Найти формулы в разделе
python main.py query formulas-in-section --section-id "chapter_глава-i-..._1-..."

# Использования символа
python main.py query symbol-usage --latex "\varepsilon_i"

# Самые цитируемые источники
python main.py query top-cited --limit 10
```

### Экспорт

```bash
# Экспорт в JSON
python main.py export json -o graph.json

# Экспорт в GraphML
python main.py export graphml -o graph.graphml

# Глоссарий символов
python main.py export glossary -o glossary.md

# Указатель формул
python main.py export formula-index -o formulas.md
```

## Прямые запросы к Neo4j

### Neo4j Browser

Откройте http://localhost:7474 и выполните Cypher запросы:

```cypher
// Найти все формулы
MATCH (f:Formula) RETURN f LIMIT 25

// Граф главы
MATCH (ch:Chapter {order: 1})-[:HAS_SECTION]->(s:Section)
RETURN ch, s

// Формулы с символами
MATCH (f:Formula)-[:USES_SYMBOL]->(s:Symbol)
RETURN f, s LIMIT 50

// Цитируемость литературы
MATCH (l:Literature)<-[:CITES]-(p:Paragraph)
RETURN l.number, l.title, count(p) as citations
ORDER BY citations DESC
```

## Структура данных

### Узлы (Nodes)

- **Book** - книга
- **Chapter** - глава
- **Section** - раздел (параграф)
- **Paragraph** - параграф текста
- **Formula** - формула
- **Symbol** - символ/обозначение
- **Illustration** - иллюстрация
- **Table** - таблица
- **Literature** - литературный источник

### Связи (Relationships)

- `HAS_CHAPTER` - книга содержит главу
- `HAS_SECTION` - глава содержит раздел
- `HAS_PARAGRAPH` - раздел содержит параграф
- `CONTAINS_FORMULA` - параграф содержит формулу
- `USES_SYMBOL` - формула использует символ
- `CONTAINS_ILLUSTRATION` - параграф содержит иллюстрацию
- `CONTAINS_TABLE` - параграф содержит таблицу
- `CITES` - параграф цитирует литературу
- `NEXT` / `PREVIOUS` - последовательные связи

## Примеры использования

### 1. Анализ использования символов

```python
from src.queries.graph_queries import GraphQueries

queries = GraphQueries(neo4j_conn)
results = queries.symbol_usage("\\varepsilon_i")

for r in results:
    print(f"{r['section_title']}: {r['formula']}")
```

### 2. Трассировка выводов формул

```cypher
MATCH path = (f1:Formula {metadata: {equation_number: '(1.25)'}})-[:DERIVED_FROM*]->(f2:Formula)
RETURN path
```

### 3. Поиск связанных разделов

```cypher
MATCH (s1:Section)-[:HAS_PARAGRAPH]->(:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)<-[:CONTAINS_FORMULA]-(:Paragraph)<-[:HAS_PARAGRAPH]-(s2:Section)
WHERE s1 <> s2
RETURN s1.title, s2.title, count(f) as shared_formulas
ORDER BY shared_formulas DESC
LIMIT 10
```

## Расширение функциональности

### Добавление нового типа узлов

1. Добавьте модель в `src/models/nodes.py`
2. Создайте импортер в `src/importers/`
3. Добавьте команду в `main.py`

### Добавление новых запросов

1. Добавьте метод в `src/queries/graph_queries.py`
2. Добавьте CLI команду в `main.py`

## Устранение неполадок

### Ошибка подключения к Neo4j

```bash
# Проверьте, что Neo4j запущен
neo4j status

# Проверьте настройки в config/config.yml
# Убедитесь, что порты 7474 и 7687 доступны
```

### Медленный импорт

```yaml
# Увеличьте batch_size в config/config.yml
import:
  batch_size: 500  # по умолчанию 100
```

### Очистка базы данных

```bash
python main.py import all --clear-database
```

⚠️ **Внимание:** Это удалит все данные из Neo4j!
