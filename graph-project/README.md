## 🔍 Примеры Cypher запросов

Откройте Neo4j Browser (http://localhost:7474) и выполните:

```cypher
// Навигация по параграфам секции
MATCH (s:Section)-[:HAS_PARAGRAPH]->(first:Paragraph)
WHERE NOT exists((first)<-[:NEXT]-())
  AND s.id STARTS WITH "chapter_глава-i"
MATCH path = (first)-[:NEXT*0..10]->(p:Paragraph)
RETURN p.order, left(p.content, 100) as preview
ORDER BY p.order;

// Найти все формулы в разделе
MATCH (s:Section {id: 'section_id'})-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
RETURN f.latex, f.metadata.equation_number
ORDER BY f.metadata.equation_number;

// Топ-10 используемых символов
MATCH (s:Symbol)<-[:USES_SYMBOL]-(f:Formula)
WITH s, count(f) as usage_count
RETURN s.latex, s.description, usage_count
ORDER BY usage_count DESC
LIMIT 10;

// Самые цитируемые источники
MATCH (l:Literature)<-[:CITES]-(p:Paragraph)
WITH l, count(p) as citation_count
RETURN l.author, l.title, citation_count
ORDER BY citation_count DESC
LIMIT 10;

// Связи между разделами через общие формулы
MATCH (s1:Section)-[:HAS_PARAGRAPH]->(:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)<-[:CONTAINS_FORMULA]-(:Paragraph)<-[:HAS_PARAGRAPH]-(s2:Section)
WHERE s1 <> s2
WITH s1, s2, count(DISTINCT f) as shared_formulas
WHERE shared_formulas > 2
RETURN s1.title, s2.title, shared_formulas
ORDER BY shared_formulas DESC
LIMIT 10;
```

**Больше примеров** в файле [`CYPHER_QUERIES.md`](CYPHER_QUERIES.md) - 22 готовых запроса для навигации, анализа и экспорта данных.# Граф Знаний - Физика Базиева

Проект для построения и работы с графом знаний научной книги "Физика Базиева".

## 🎯 Возможности

- ✅ **Импорт структурированных данных** - Book, Chapter, Section, Paragraph
- ✅ **Семантические артефакты** - ~1000+ формул, ~200+ символов, ~65 иллюстраций, ~36 таблиц, ~48 источников литературы
- ✅ **Связывание контента** - автоматическое создание связей между параграфами, формулами, символами и литературой
- ✅ **Мощные запросы** - готовые Cypher и Python запросы для анализа
- ✅ **Экспорт** - JSON, GraphML, Markdown (глоссарий, указатель формул)
- ✅ **CLI интерфейс** - удобная работа через командную строку
- ✅ **Визуализация** - интерактивные графы (опционально)

## 📊 Архитектура графа

Проект реализует граф знаний согласно спецификации в [`normalized/graph-arch.md`](../normalized/graph-arch.md).

### Типы узлов

- **Структурные**: Book, Chapter, Section, Subsection, Paragraph
- **Семантические**: Formula, Symbol, Illustration, Table, Literature
- **Концептуальные**: Concept, PhysicalQuantity, Law (для будущего расширения)

### Типы связей

- **Структурные**: `HAS_CHAPTER`, `HAS_SECTION`, `HAS_PARAGRAPH`, `NEXT`
- **Семантические**: `CONTAINS_FORMULA`, `USES_SYMBOL`, `CONTAINS_ILLUSTRATION`, `CONTAINS_TABLE`, `CITES`
- **Концептуальные**: `DEFINES`, `MENTIONS`, `RELATED_TO` (для будущего расширения)

**Новое**: связи `NEXT` обеспечивают навигацию по последовательности параграфов и секций, что позволяет легко читать контент в правильном порядке и визуализировать структуру документа.

## 🛠️ Технологии

- **Python 3.8+**
- **Neo4j 5.x** - графовая база данных
- **APOC** - Awesome Procedures On Cypher (required for graph schema operations)
- **neo4j-driver** - Python драйвер
- **Click** - CLI интерфейс
- **PyYAML** - конфигурация
- **tqdm** - прогресс-бары
- **pytest** - тестирование

## 📈 Статистика

После импорта всех данных граф содержит:

- **Узлы**: 17,154
  - Book: 1
  - Chapter: 15
  - Section: 43
  - Paragraph: 6,921
  - Formula: 9,815
  - Symbol: 206
  - Illustration: 69
  - Table: 36
  - Literature: 48

- **Связи**: 23,756
  - HAS_CHAPTER: 15
  - HAS_SECTION: 43
  - HAS_PARAGRAPH: 6,921
  - NEXT: 6,925 (6,878 между параграфами + 33 между секциями)
  - CONTAINS_FORMULA: 5,730
  - CONTAINS_TABLE: 36 (22 от Paragraph + 14 от Chapter)
  - CONTAINS_ILLUSTRATION: 69
  - CITES: 32

**Особенности импорта**:
- Все 36 таблиц имеют связи (100% покрытие)
- Все 69 иллюстраций имеют связи (100% покрытие)
- 5,722 формулы связаны с параграфами (~58% покрытие)
- 23 источника литературы цитируются в тексте

**Проверка статистики**:
```bash
python graph_stats.py
```

- **Размер базы**: ~100-500 MB

## 🧪 Тестирование

```bash
pytest tests/
```

## 🚧 Будущие улучшения

- [ ] NLP анализ для автоматического извлечения концепций
- [ ] GraphQL API для веб-интерфейса
- [ ] Машинное обучение для рекомендаций
- [ ] Версионирование изменений
- [ ] Экспорт в RDF/Turtle для семантического веба
- [ ] Интеграция с внешними источниками (Wikipedia, arXiv)

## 📝 Структура проекта

```
graph-project/
├── config/              # Конфигурационные файлы
├── src/
│   ├── models/          # Модели узлов графа
│   ├── importers/       # Импортеры данных в граф
│   ├── queries/         # Готовые запросы к графу
│   └── utils/           # Вспомогательные утилиты
├── tests/               # Тесты
├── requirements.txt     # Python зависимости
└── main.py             # Главный скрипт

```

## 🚀 Быстрый старт

### 1. Установите Neo4j

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
  -e NEO4J_PLUGINS='["apoc"]' \
  -e NEO4J_apoc_export_file_enabled=true \
  -e NEO4J_apoc_import_file_enabled=true \
  -v $PWD/neo4j-data:/data \
  neo4j:latest
```

### 1.5. Установите APOC (обязательно)

APOC (Awesome Procedures On Cypher) требуется для работы с графом:

```bash
cd graph-project
./install_apoc.sh
```

Или следуйте подробным инструкциям в [APOC_SETUP.md](APOC_SETUP.md).

Проверьте установку:
```bash
python verify_apoc.py
```

### 2. Настройте проект

```bash
cd graph-project
./setup.sh
```

### 3. Настройте конфигурацию

Отредактируйте `config/config.yml`:
```yaml
neo4j:
  uri: "bolt://localhost:7687"
  username: "neo4j"
  password: "ваш_пароль"  # измените!
  database: "baziev"

paths:
  # Путь к документам со ссылками на сущности {{formula:id}}, {{symbol:id}} и т.д.
  docs: "../normalized/step-05-extract-and-link-quoted-literature/result"
```

### 4. Проверьте установку

```bash
python check.py
```

### 5. Импортируйте данные

```bash
source venv/bin/activate
python main.py import all
```

Это займёт ~5-15 минут в зависимости от производительности системы.

## 💻 Использование

### Импорт данных

```bash
# Импортировать все данные
python main.py import all

# Или поэтапно:
python main.py import structure      # Структура (Book, Chapter)
python main.py import formulas       # ~1000+ формул
python main.py import symbols        # ~200+ символов
python main.py import illustrations  # ~65 иллюстраций
python main.py import tables         # ~36 таблиц
python main.py import literature     # ~48 источников
python main.py import paragraphs     # Параграфы из markdown
python main.py import link-content   # Связывание контента
python main.py import sequence       # Создание связей NEXT между параграфами и секциями
```

### Запросы к графу

```bash
# Показать статистику
python main.py stats

# Статистика по главам
python main.py query chapter-stats

# Найти формулы в разделе
python main.py query formulas-in-section --section-id "section_id"

# Использования символа
python main.py query symbol-usage --latex "\\varepsilon_i"

# Топ-10 цитируемых источников
python main.py query top-cited --limit 10
```

### Экспорт данных

```bash
# Экспорт в JSON
python main.py export json -o graph.json

# Экспорт в GraphML (для Gephi, Cytoscape)
python main.py export graphml -o graph.graphml

# Глоссарий символов
python main.py export glossary -o glossary.md

# Указатель формул
python main.py export formula-index -o formulas.md
```

### Примеры использования API

```bash
python examples.py
```

## 📚 Документация

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - подробная архитектура проекта
- **[USAGE.md](USAGE.md)** - руководство по использованию
- **[graph-arch.md](../normalized/graph-arch.md)** - спецификация графа знаний
- **[examples.py](examples.py)** - примеры работы с API
- **[src/queries/examples.cypher](src/queries/examples.cypher)** - примеры Cypher запросов

## 🤝 Вклад в проект

Приветствуются pull requests и issue reports!

## 📄 Лицензия

MIT

---

**Создано:** 25 октября 2025  
**Версия:** 1.0.0
