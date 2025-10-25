# Архитектура графа знаний книги "Физика Базиева"

## Обзор

Данная архитектура описывает модель связанного графа для представления научной книги в виде семантической сети, где все элементы контента связаны между собой через явные отношения.

## Основные типы узлов (Node Types)

> **Примечание:** Все семантические артефакты хранятся в директории `normalized/` в виде JSON файлов:
> - Формулы: `normalized/formulas/formula_{hash}.json` (~1000+ файлов)
> - Иллюстрации: `normalized/illustrations/illustration_{hash}.json` (~65 файлов)
> - Символы: `normalized/symbols/symbol_{hash}.json` (~200+ файлов)
> - Таблицы: `normalized/tables/table_{hash}.json` (~36 файлов)
> - Литература: `normalized/literature/literature_{hash}.json` (~48 файлов)

### 1. Структурные узлы

#### 1.1. Book (Книга)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `title`: название книги
  - `author`: автор
  - `description`: описание

#### 1.2. Chapter (Глава)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `title`: название главы
  - `order`: порядковый номер
  - `file_path`: путь к файлу
  
#### 1.3. Section (Параграф/Раздел)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `title`: название параграфа
  - `number`: номер параграфа (например, "§ 1")
  - `order`: порядковый номер в главе
  - `file_path`: путь к файлу
  - `position`: позиция в исходном файле

#### 1.4. Subsection (Подраздел)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `title`: название подраздела
  - `level`: уровень заголовка (h3, h4, и т.д.)
  - `order`: порядковый номер в секции

#### 1.5. Paragraph (Абзац/Текстовый блок)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `content`: текстовое содержание
  - `order`: порядковый номер
  - `word_count`: количество слов

### 2. Семантические узлы контента

#### 2.1. Formula (Формула)
- **Свойства:**
  - `id`: уникальный идентификатор (hash из 12 символов)
  - `type`: тип формулы (`inline` | `block`)
  - `latex`: LaTeX представление
  - `metadata`: объект с полями {db_key, src, equation_number}
  - `source`: объект {file, position} - местоположение в markdown
  - `symbols`: массив ID используемых символов
  - `wrapper_html`: HTML-обёртка для отображения

- **Расположение:** `normalized/formulas/`
- **Формат файла:** `formula_{hash}.json`
- **Пример:** `formula_000a0fda1c13.json`
  ```json
  {
    "id": "000a0fda1c13",
    "type": "inline",
    "latex": "OO_1 = \\Delta l. \\quad OO_3 = \\lambda/2",
    "metadata": {
      "db_key": "3703",
      "src": "images/formula_inline_231_4_1.webp",
      "equation_number": null
    },
    "source": {
      "file": "chapter_глава-i-.../14-генерация-энергии-и-светла.md",
      "position": 76318
    },
    "symbols": []
  }
  ```
  
#### 2.2. Symbol (Символ/Обозначение)
- **Свойства:**
  - `id`: уникальный идентификатор (hash из 12 символов)
  - `latex`: LaTeX представление символа
  - `description`: текстовое описание значения
  - `metadata`: объект {db_key, src}

- **Расположение:** `normalized/symbols/`
- **Формат файла:** `symbol_{hash}.json`
- **Пример:** `symbol_006274a1b4b0.json`
  ```json
  {
    "id": "006274a1b4b0",
    "latex": "\\varepsilon_i",
    "description": "электрическая проницаемость i-го вещества",
    "metadata": {
      "db_key": "9298",
      "src": "images/formula_inline_627_1_87.webp"
    }
  }
  ```

#### 2.3. Illustration (Иллюстрация)
- **Свойства:**
  - `id`: уникальный идентификатор (hash из 12 символов)
  - `type`: тип иллюстрации (`svg` обычно)
  - `svg_content`: полный SVG контент
  - `caption`: текст подписи к иллюстрации
  - `metadata`: объект {db_key, src, svg_id, svg_viewbox, element_counts, has_caption, caption_has_formulas, caption_formula_refs, wrapper_type}
  - `source`: объект {file, position}
  - `wrapper_html`: HTML-обёртка с подписью

- **Расположение:** `normalized/illustrations/`
- **Формат файла:** `illustration_{hash}.json`
- **Пример:** `illustration_0371e37cbf14.json`
  ```json
  {
    "id": "0371e37cbf14",
    "type": "svg",
    "svg_content": "<svg id=\"uuid-c9e4f94d-...\" ...>...</svg>",
    "caption": "Рис. 31. Вход в тот же межатомный канал...",
    "metadata": {
      "db_key": "5979",
      "has_caption": true,
      "caption_has_formulas": false,
      "element_counts": {"circle": 5, "line": 4, "text": 5, "rect": 1}
    },
    "source": {
      "file": "chapter_глаза-iv-.../20-природа-удельного-сопротивления...",
      "position": 39682
    }
  }
  ```

#### 2.4. Table (Таблица)
- **Свойства:**
  - `id`: уникальный идентификатор (hash из 12 символов)
  - `type`: тип таблицы (`markdown` обычно)
  - `content`: объект {raw, headers, rows}
  - `metadata`: объект {row_count, column_count, has_formulas, formula_refs}
  - `source`: объект {file, position}
  - `html_attributes`: дополнительные HTML атрибуты (если есть)

- **Расположение:** `normalized/tables/`
- **Формат файла:** `table_{hash}.json`
- **Пример:** `table_1089d2d169b9.json`
  ```json
  {
    "id": "1089d2d169b9",
    "type": "markdown",
    "content": {
      "raw": "| Элемент | Избыточный заряд, Кл | Валентность |\n...",
      "headers": ["Элемент", "Избыточный заряд, Кл", "Валентность"],
      "rows": [["Li", "-8,8617997·10⁻²⁰", "-1,1062113"], ...]
    },
    "metadata": {
      "row_count": 8,
      "column_count": 3,
      "has_formulas": false
    },
    "source": {
      "file": "chapter_глава-v-.../23-зарядовая-структура-атома...",
      "position": 127873
    }
  }
  ```

#### 2.5. Literature (Литература)
- **Свойства:**
  - `id`: уникальный идентификатор (hash из 12 символов)
  - `number`: порядковый номер в списке литературы
  - `text`: полный текст библиографической записи
  - `author`: автор (извлечено)
  - `title`: название работы (извлечено)
  - `publication`: издательство и год (извлечено)
  - `source`: объект {file, position}

- **Расположение:** `normalized/literature/`
- **Формат файла:** `literature_{hash}.json`
- **Пример:** `literature_00f14c9e26cb.json`
  ```json
  {
    "id": "00f14c9e26cb",
    "number": 26,
    "text": "В. 3. Красин. Сверхпроводимость и сверхтекучесть. М., Наука, 1978.",
    "author": "В",
    "title": "3. Красин. Сверхпроводимость и сверхтекучесть.",
    "publication": "М., Наука, 1978.",
    "source": {
      "file": "docs/chapter_список-цитированной-литературы/index.md",
      "position": 1948
    }
  }
  ```

### 3. Концептуальные узлы

#### 3.1. Concept (Концепция/Термин)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `name`: название концепции
  - `definition`: определение
  - `aliases`: альтернативные названия (массив)
  - `category`: категория (физическая величина, явление, закон, и т.д.)

#### 3.2. PhysicalQuantity (Физическая величина)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `name`: название величины
  - `symbol_id`: ссылка на Symbol
  - `unit`: единица измерения
  - `dimension`: размерность

#### 3.3. Law (Закон/Принцип)
- **Свойства:**
  - `id`: уникальный идентификатор
  - `name`: название закона
  - `statement`: формулировка
  - `formula_ids`: массив связанных формул

## Типы связей (Relationship Types)

### 1. Структурные связи

#### 1.1. HAS_CHAPTER
- **От:** Book → Chapter
- **Свойства:** `order` (порядковый номер)

#### 1.2. HAS_SECTION
- **От:** Chapter → Section
- **Свойства:** `order` (порядковый номер)

#### 1.3. HAS_SUBSECTION
- **От:** Section → Subsection
- **Свойства:** `order` (порядковый номер)

#### 1.4. HAS_PARAGRAPH
- **От:** Section | Subsection → Paragraph
- **Свойства:** `order` (порядковый номер)

#### 1.5. NEXT
- **От:** Chapter → Chapter | Section → Section | Paragraph → Paragraph
- **Свойства:** нет
- **Описание:** Последовательная связь элементов одного уровня

#### 1.6. PREVIOUS
- **От:** Chapter → Chapter | Section → Section | Paragraph → Paragraph
- **Свойства:** нет
- **Описание:** Обратная последовательная связь

### 2. Семантические связи контента

#### 2.1. CONTAINS_FORMULA
- **От:** Paragraph | Table | Illustration (caption) → Formula
- **Свойства:** 
  - `position`: позиция в тексте
  - `context`: окружающий текст (фрагмент)

#### 2.2. USES_SYMBOL
- **От:** Formula → Symbol
- **Свойства:** 
  - `count`: количество использований в формуле
  - `role`: роль символа (переменная, константа, оператор)

#### 2.3. CONTAINS_ILLUSTRATION
- **От:** Section | Subsection | Paragraph → Illustration
- **Свойства:** 
  - `position`: позиция в тексте
  - `reference_text`: текст ссылки на иллюстрацию

#### 2.4. CONTAINS_TABLE
- **От:** Section | Subsection | Paragraph → Table
- **Свойства:** 
  - `position`: позиция в тексте

#### 2.5. CITES
- **От:** Paragraph | Section → Literature
- **Свойства:** 
  - `position`: позиция в тексте
  - `context`: контекст цитирования

#### 2.6. REFERENCES_FORMULA
- **От:** Formula → Formula
- **Свойства:** 
  - `type`: тип связи (derived_from, equivalent_to, contradicts)
  - `description`: описание связи

#### 2.7. ILLUSTRATES_CONCEPT
- **От:** Illustration → Concept
- **Свойства:** 
  - `aspect`: какой аспект концепции иллюстрируется

#### 2.8. FORMULA_IN_CAPTION
- **От:** Illustration → Formula
- **Свойства:** 
  - `position`: позиция в подписи

#### 2.9. TABLE_CONTAINS_FORMULA
- **От:** Table → Formula
- **Свойства:** 
  - `cell_row`: номер строки
  - `cell_column`: номер столбца

### 3. Концептуальные связи

#### 3.1. DEFINES
- **От:** Section | Paragraph → Concept
- **Свойства:** 
  - `definition_type`: (formal, informal, example)
  - `completeness`: (полное, частичное)

#### 3.2. MENTIONS
- **От:** Paragraph → Concept
- **Свойства:** 
  - `count`: количество упоминаний
  - `context_type`: (definition, application, discussion, critique)

#### 3.3. RELATED_TO
- **От:** Concept → Concept
- **Свойства:** 
  - `relation_type`: (is_a, part_of, causes, affects, contradicts, similar_to)
  - `strength`: сила связи (0.0 - 1.0)

#### 3.4. FORMALIZED_BY
- **От:** Concept → Formula
- **Свойства:** 
  - `formalization_type`: (exact, approximate, special_case)

#### 3.5. DESCRIBES
- **От:** Symbol → PhysicalQuantity
- **Свойства:** нет

#### 3.6. EXPRESSED_IN
- **От:** Law → Formula
- **Свойства:** 
  - `is_primary`: флаг основной формулы закона

#### 3.7. CONTRADICTS
- **От:** Concept | Law → Concept | Law
- **Свойства:** 
  - `explanation`: объяснение противоречия
  - `resolution`: предложенное разрешение

#### 3.8. GENERALIZES
- **От:** Concept | Law → Concept | Law
- **Свойства:** 
  - `scope`: область обобщения

#### 3.9. SPECIAL_CASE_OF
- **От:** Concept | Law → Concept | Law
- **Свойства:** 
  - `conditions`: условия частного случая

### 4. Кросс-референсные связи

#### 4.1. DERIVED_FROM
- **От:** Formula → Formula
- **Свойства:** 
  - `derivation_steps`: количество шагов
  - `section_id`: где происходит вывод

#### 4.2. EQUIVALENT_TO
- **От:** Formula → Formula
- **Свойства:** 
  - `transformation`: тип преобразования

#### 4.3. SUPPORTS
- **От:** Literature → Concept | Law | Formula
- **Свойства:** 
  - `support_type`: (empirical, theoretical, historical)
  - `strength`: сила поддержки

#### 4.4. CITED_BY
- **От:** Literature → Section | Paragraph
- **Свойства:** 
  - `citation_context`: контекст цитирования
  - `citation_purpose`: (support, critique, comparison, background)

## Пример структуры графа

```
Book
 └─[HAS_CHAPTER]→ Chapter (Глава I)
    ├─[HAS_SECTION]→ Section (§1)
    │  ├─[HAS_SUBSECTION]→ Subsection (1. Состояние термодинамики газов)
    │  │  ├─[HAS_PARAGRAPH]→ Paragraph
    │  │  │  ├─[CONTAINS_FORMULA]→ Formula (1.1: PV = nRT)
    │  │  │  │  └─[USES_SYMBOL]→ Symbol (P, V, n, R, T)
    │  │  │  ├─[MENTIONS]→ Concept (Идеальный газ)
    │  │  │  └─[CITES]→ Literature (М. Планк, 1900)
    │  │  └─[DEFINES]→ Concept (Глобула)
    │  └─[NEXT]→ Section (§2)
    └─[NEXT]→ Chapter (Глава II)

Formula (1.2)
 ├─[DERIVED_FROM]→ Formula (1.1)
 ├─[USES_SYMBOL]→ Symbol (ε, V_г)
 └─[FORMALIZED_BY]← Concept (Кинетическая энергия осциллятора)

Illustration (Рис. 31)
 ├─[CONTAINS_FORMULA]→ Formula (в подписи)
 ├─[ILLUSTRATES_CONCEPT]→ Concept (Сверхпроводимость)
 └─[CONTAINED_IN]← Section (§20)
```

## Метаданные и индексы

### Индексы для поиска
1. **Полнотекстовый индекс** по содержанию параграфов
2. **LaTeX индекс** для поиска формул
3. **Символьный индекс** для быстрого поиска обозначений
4. **Концептуальный индекс** для тематического поиска
5. **Индекс литературы** по авторам и названиям

### Вычисляемые метрики узлов
1. **PageRank** - важность концепции/раздела
2. **Degree centrality** - количество связей
3. **Betweenness centrality** - роль в связывании концепций
4. **Community detection** - группировка связанных концепций
5. **Citation count** - частота цитирования

## Практические применения графа

### 1. Навигация и исследование
- Интерактивная визуализация связей между концепциями
- Поиск всех мест, где используется формула или символ
- Трассировка выводов формул через граф
- Построение карты зависимостей между главами

### 2. Семантический поиск
- Поиск по концепциям, а не только по ключевым словам
- Поиск похожих разделов по структуре связей
- Поиск противоречий в теории
- Рекомендации связанного контента

### 3. Анализ и валидация
- Проверка полноты определений
- Поиск неиспользуемых символов
- Анализ цитируемости литературы
- Выявление изолированных концепций

### 4. Обучение и понимание
- Построение индивидуальных траекторий обучения
- Визуализация структуры знаний
- Генерация вопросов по концепциям
- Создание интерактивных упражнений

### 5. Экспорт и интеграция
- Генерация глоссария с обратными ссылками
- Создание интерактивного указателя формул
- Построение карты литературы с аннотациями
- Экспорт в различные форматы (JSON-LD, RDF, GraphML)

## Технические рекомендации

### Хранилище графа
- **Neo4j** - рекомендуемая графовая БД (поддержка Cypher, визуализация, масштабируемость)
- **ArangoDB** - альтернатива с поддержкой мультимодели
- **PostgreSQL + Apache AGE** - решение на базе реляционной БД

### Формат обмена
- **JSON-LD** для сериализации с поддержкой Linked Data
- **GraphML** для визуализации в специализированных инструментах
- **RDF/Turtle** для семантического веба

### API и интерфейсы
- **GraphQL** API для гибких запросов к графу
- **REST API** для базовых операций CRUD
- **Cypher endpoint** для прямых запросов к Neo4j

## Структура исходных файлов

### Markdown файлы книги

- **Расположение:** `docs/` и `normalized/step-05-extract-and-link-quoted-literature/result/`
- **Структура глав:**
  ```
  docs/
    index.md
    chapter_глава-i-система-новейших-фундаментальных-открытий/
      index.md
      1-гиперчастотная-механика-или-механика-микромира.md
      2-электрино-вторая-и-последняя-истинно-элементарная-частица.md
      ...
    chapter_глава-ii-основы-строения-твердого-тела/
      index.md
      15-золото-как-типичная-кристаллическая-структура.md
    chapter_глава-iii-структура-жидкостей-и-паров/
      16-пар-второе-состояние-воды.md
      17-вода-как-типичная-жидкость.md
      18-фазовые-переходы-воды.md
    ...
  ```

### Вложения в markdown файлах

- **Формулы:** `{{formula:000a0fda1c13}}`
- **Иллюстрации:** `{{illustration:0371e37cbf14}}`
- **Символы:** `{{symbol:006274a1b4b0}}`
- **Таблицы:** `{{table:1089d2d169b9}}`
- **Литература:** `{{literature:00f14c9e26cb}}`

### Статистика артефактов

| Тип артефакта | Количество файлов | Примерная оценка |
|---|---|---|
| Формулы | ~1000+ | Основной тип контента |
| Иллюстрации | ~65 | SVG диаграммы и графики |
| Символы | ~200+ | Физические обозначения |
| Таблицы | ~36 | Численные данные |
| Литература | ~48 | Цитируемые источники |

## Миграция данных

### Этапы построения графа

1. **Импорт структурных узлов**
   - Создание узлов Book, Chapter, Section
   - Установка связей HAS_CHAPTER, HAS_SECTION
   - Источник: структура директорий `docs/chapter_*/`

2. **Импорт семантических артефактов**
   - Загрузка Formula из `normalized/formulas/*.json` (~1000+ файлов)
   - Загрузка Illustration из `normalized/illustrations/*.json` (~65 файлов)
   - Загрузка Symbol из `normalized/symbols/*.json` (~200+ файлов)
   - Загрузка Table из `normalized/tables/*.json` (~36 файлов)
   - Загрузка Literature из `normalized/literature/*.json` (~48 файлов)

3. **Парсинг markdown файлов**
   - Извлечение параграфов из `docs/**/*.md`
   - Анализ заголовков для создания Section и Subsection
   - Парсинг текстовых блоков для Paragraph
   - Установка связей HAS_PARAGRAPH

4. **Связывание контента**
   - Поиск вхождений `{{formula:hash}}` в параграфах → CONTAINS_FORMULA
   - Поиск вхождений `{{illustration:hash}}` → CONTAINS_ILLUSTRATION
   - Поиск вхождений `{{table:hash}}` → CONTAINS_TABLE
   - Поиск вхождений `{{literature:hash}}` → CITES
   - Связывание символов с формулами через поле `symbols` → USES_SYMBOL
   - Связывание иллюстраций с формулами через `caption_formula_refs` → FORMULA_IN_CAPTION
   - Связывание таблиц с формулами через `formula_refs` → TABLE_CONTAINS_FORMULA

5. **Извлечение концепций** (NLP)
   - Идентификация терминов и концепций
   - Создание узлов Concept
   - Установка связей DEFINES, MENTIONS

6. **Построение семантических связей**
   - Анализ выводов формул → DERIVED_FROM
   - Анализ отношений концепций → RELATED_TO
   - Идентификация законов → EXPRESSED_IN

7. **Индексирование и оптимизация**
   - Создание индексов для быстрого поиска
   - Вычисление метрик центральности
   - Предварительный расчет популярных запросов

## Схема свойств в Neo4j

### Ограничения (Constraints)

```cypher
// Уникальность ID
CREATE CONSTRAINT formula_id IF NOT EXISTS FOR (f:Formula) REQUIRE f.id IS UNIQUE;
CREATE CONSTRAINT symbol_id IF NOT EXISTS FOR (s:Symbol) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT illustration_id IF NOT EXISTS FOR (i:Illustration) REQUIRE i.id IS UNIQUE;
CREATE CONSTRAINT literature_id IF NOT EXISTS FOR (l:Literature) REQUIRE l.id IS UNIQUE;
CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE;
```

### Индексы

```cypher
// Полнотекстовый поиск
CREATE FULLTEXT INDEX paragraph_content IF NOT EXISTS FOR (p:Paragraph) ON EACH [p.content];
CREATE FULLTEXT INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON EACH [c.name, c.definition];

// Обычные индексы
CREATE INDEX formula_latex IF NOT EXISTS FOR (f:Formula) ON (f.latex);
CREATE INDEX symbol_latex IF NOT EXISTS FOR (s:Symbol) ON (s.latex);
CREATE INDEX literature_number IF NOT EXISTS FOR (l:Literature) ON (l.number);
```

## Примеры запросов Cypher

### 1. Найти все формулы в разделе
```cypher
MATCH (s:Section {id: 'section_1'})-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
RETURN f.latex, f.equation_number
ORDER BY f.equation_number
```

### 2. Трассировка вывода формулы
```cypher
MATCH path = (f1:Formula {equation_number: '(1.25)'})-[:DERIVED_FROM*]->(f2:Formula)
RETURN path
```

### 3. Найти все использования символа
```cypher
MATCH (s:Symbol {latex: '\\varepsilon_i'})<-[:USES_SYMBOL]-(f:Formula)<-[:CONTAINS_FORMULA]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(sec:Section)
RETURN sec.title, f.equation_number, f.latex
```

### 4. Поиск связанных концепций
```cypher
MATCH (c1:Concept {name: 'Глобула'})-[r:RELATED_TO]-(c2:Concept)
RETURN c2.name, r.relation_type, r.strength
ORDER BY r.strength DESC
```

### 5. Самые цитируемые источники
```cypher
MATCH (l:Literature)<-[:CITES]-(p:Paragraph)
WITH l, count(p) as citation_count
RETURN l.author, l.title, citation_count
ORDER BY citation_count DESC
LIMIT 10
```

### 6. Найти разделы, использующие определенную концепцию
```cypher
MATCH (c:Concept {name: 'Осциллятор'})<-[:MENTIONS]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(s:Section)
RETURN DISTINCT s.title, s.file_path
```

### 7. Иллюстрации с формулами в подписи
```cypher
MATCH (i:Illustration)-[:FORMULA_IN_CAPTION]->(f:Formula)
RETURN i.caption, f.latex, f.equation_number
```

## Расширения и будущие возможности

1. **Временная ось**: связывание концепций с историческим контекстом
2. **Мультиязычность**: поддержка переводов с сохранением графовой структуры
3. **Версионирование**: отслеживание изменений в концепциях и формулах
4. **Аннотации пользователей**: добавление заметок и комментариев к узлам
5. **Машинное обучение**: автоматическая классификация концепций, предсказание связей
6. **Интеграция с внешними источниками**: связывание с Wikipedia, arXiv, DOI
7. **Collaborative filtering**: рекомендации на основе поведения пользователей

---

*Документ создан: 25 октября 2025*
*Версия: 1.0*
