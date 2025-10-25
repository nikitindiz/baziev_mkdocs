# Архитектура Graph Project

## Обзор

Graph Project - это система для построения и работы с графом знаний научной книги "Физика Базиева". Проект реализован на Python с использованием Neo4j в качестве графовой базы данных.

## Технологический стек

- **Python 3.8+** - основной язык программирования
- **Neo4j 5.x** - графовая база данных
- **neo4j-driver** - Python драйвер для Neo4j
- **Click** - CLI фреймворк
- **PyYAML** - работа с конфигурацией
- **tqdm** - прогресс-бары для импорта
- **pytest** - тестирование

## Архитектура проекта

```
graph-project/
├── config/                 # Конфигурационные файлы
│   └── config.yml         # Основная конфигурация
│
├── src/                   # Исходный код
│   ├── models/           # Модели данных
│   │   └── nodes.py      # Dataclass модели для узлов графа
│   │
│   ├── importers/        # Импортеры данных
│   │   ├── structure_importer.py   # Импорт структуры (Book, Chapter)
│   │   ├── artifacts_importer.py   # Импорт артефактов (Formula, Symbol, etc.)
│   │   └── content_linker.py       # Парсинг markdown и связывание
│   │
│   ├── queries/          # Запросы к графу
│   │   ├── graph_queries.py        # Python класс с готовыми запросами
│   │   └── examples.cypher         # Примеры Cypher запросов
│   │
│   └── utils/            # Утилиты
│       ├── config.py              # Загрузка конфигурации
│       ├── neo4j_connection.py    # Подключение к Neo4j
│       ├── exporter.py            # Экспорт графа
│       └── visualizer.py          # Визуализация
│
├── tests/                # Тесты
│   └── test_graph.py
│
├── main.py              # Главный CLI скрипт
├── examples.py          # Примеры использования
├── setup.sh            # Установочный скрипт
└── requirements.txt    # Python зависимости
```

## Компоненты системы

### 1. Модели данных (src/models/)

Определяют структуру узлов графа:

- **Book** - книга
- **Chapter** - глава
- **Section** - раздел
- **Paragraph** - параграф
- **Formula** - формула
- **Symbol** - символ
- **Illustration** - иллюстрация
- **Table** - таблица
- **Literature** - литература
- **Concept** - концепция (для будущего расширения)

### 2. Импортеры (src/importers/)

#### StructureImporter
Отвечает за импорт структурных элементов:
- Создание узла Book
- Сканирование директорий docs/ и создание Chapter узлов
- Установка связей HAS_CHAPTER, NEXT, PREVIOUS

#### ArtifactsImporter
Импортирует семантические артефакты из JSON файлов:
- Formula из `normalized/formulas/*.json`
- Symbol из `normalized/symbols/*.json`
- Illustration из `normalized/illustrations/*.json`
- Table из `normalized/tables/*.json`
- Literature из `normalized/literature/*.json`

Использует батч-импорт для оптимизации производительности.

#### ContentLinker
Парсит markdown файлы и создаёт связи:
- Извлекает Section и Paragraph из markdown
- Находит вхождения {{formula:id}}, {{illustration:id}}, и т.д.
- Создаёт связи CONTAINS_FORMULA, CONTAINS_ILLUSTRATION, CITES

### 3. Запросы (src/queries/)

#### GraphQueries
Python класс с готовыми методами для типовых запросов:
- `formulas_in_section()` - формулы в разделе
- `symbol_usage()` - использование символа
- `top_cited_literature()` - топ цитируемых источников
- `chapter_statistics()` - статистика по главам
- и другие...

#### examples.cypher
Файл с примерами Cypher запросов для прямого использования в Neo4j Browser.

### 4. Утилиты (src/utils/)

#### Neo4jConnection
Обёртка над neo4j-driver с дополнительными методами:
- Выполнение запросов
- Создание ограничений и индексов
- Получение статистики
- Очистка базы данных

#### Config
Загрузка конфигурации из YAML и переменных окружения.

#### GraphExporter
Экспорт графа в различные форматы:
- JSON
- GraphML
- Markdown (глоссарий, указатель формул)

#### GraphVisualizer
Визуализация графа с использованием pyvis:
- Структура главы
- Зависимости формул
- Карта концепций

### 5. CLI (main.py)

Главный интерфейс командной строки с группами команд:

**import** - импорт данных:
- `all` - импортировать всё
- `structure` - только структуру
- `formulas`, `symbols`, etc. - отдельные типы
- `paragraphs` - параграфы из markdown
- `link-content` - связывание контента

**query** - запросы:
- `formulas-in-section`
- `symbol-usage`
- `top-cited`
- `chapter-stats`

**export** - экспорт:
- `json`, `graphml` - форматы графов
- `glossary`, `formula-index` - документация

**stats** - показать статистику графа

## Процесс импорта данных

### Этап 1: Структура
```
Book (1 узел)
  └─ HAS_CHAPTER → Chapter (10+ узлов)
       └─ NEXT → Chapter
```

### Этап 2: Артефакты
```
Formula (~1000+ узлов)
Symbol (~200+ узлов)
Illustration (~65 узлов)
Table (~36 узлов)
Literature (~48 узлов)
```

### Этап 3: Контент
```
Chapter
  └─ HAS_SECTION → Section (много узлов)
       └─ HAS_PARAGRAPH → Paragraph (очень много узлов)
```

### Этап 4: Связывание
```
Paragraph
  ├─ CONTAINS_FORMULA → Formula
  ├─ CONTAINS_ILLUSTRATION → Illustration
  ├─ CONTAINS_TABLE → Table
  └─ CITES → Literature

Formula
  └─ USES_SYMBOL → Symbol
```

## Оптимизации

### 1. Батч-импорт
Артефакты импортируются партиями (batch_size = 100) для уменьшения количества транзакций.

### 2. Индексы
Создаются индексы для быстрого поиска:
- Уникальные ID для всех типов узлов
- Полнотекстовый индекс для параграфов
- Индексы на LaTeX, номера формул, и т.д.

### 3. Ограничения
Ограничения уникальности предотвращают дубликаты:
```cypher
CREATE CONSTRAINT formula_id IF NOT EXISTS 
FOR (f:Formula) REQUIRE f.id IS UNIQUE
```

## Расширяемость

### Добавление новых типов узлов

1. Добавьте dataclass в `src/models/nodes.py`:
```python
@dataclass
class NewNode:
    id: str
    property1: str
    property2: int
```

2. Создайте импортер в `src/importers/`:
```python
def import_new_nodes(self):
    # Логика импорта
    pass
```

3. Добавьте команду в `main.py`:
```python
@import_cmd.command('new-nodes')
def import_new_nodes(ctx):
    # Вызов импортера
    pass
```

### Добавление новых запросов

1. Добавьте метод в `GraphQueries`:
```python
def custom_query(self, param):
    query = "MATCH ... RETURN ..."
    return self.conn.execute_query(query, {"param": param})
```

2. Добавьте CLI команду:
```python
@query.command('custom')
def custom_query_cmd(ctx, param):
    results = queries.custom_query(param)
    # Вывод результатов
```

## Безопасность

- Пароли хранятся в `.env` (не коммитится в git)
- Используется параметризация запросов для предотвращения инъекций
- Настройки доступа к Neo4j изолированы в конфигурации

## Производительность

### Ожидаемое время импорта
- Структура: ~1 секунда
- Артефакты: ~10-30 секунд (зависит от количества)
- Параграфы: ~1-5 минут
- Связывание: ~2-10 минут

### Объём данных
- Узлов: ~3000-5000
- Связей: ~10000-20000
- Размер базы: ~100-500 MB

## Мониторинг и отладка

### Логирование
Все операции логируются с уровнями:
- INFO - успешные операции
- WARNING - потенциальные проблемы
- ERROR - ошибки импорта/запросов

### Статистика
Команда `stats` показывает количество узлов каждого типа и связей.

### Neo4j Browser
http://localhost:7474 - визуальный интерфейс для исследования графа.

## Будущие улучшения

1. **NLP анализ** - автоматическое извлечение концепций
2. **GraphQL API** - веб-интерфейс для запросов
3. **Машинное обучение** - рекомендации связанного контента
4. **Версионирование** - отслеживание изменений
5. **Экспорт в RDF** - семантический веб
