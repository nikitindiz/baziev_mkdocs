# Paragraph Context API

## Эндпоинт

```
GET /api/paragraphs/[id]/context
```

## Описание

Этот эндпоинт возвращает полный контекст абзаца, включая:
- Информацию о главе, к которой принадлежит абзац
- Информацию о секции, к которой принадлежит абзац
- Все абзацы секции в правильном порядке с их контентом
- Связи абзацев с таблицами, иллюстрациями и формулами
- Метаданные о предыдущей и следующей главах

## Параметры

### Path параметры

- `id` (string, обязательный) - ID абзаца

## Пример запроса

```bash
curl http://localhost:3000/api/paragraphs/chapter_глава-i-система-новейших-фундаментальных-открытий_9-фазовый-переход-высшего-рода_p0/context
```

## Пример ответа

```json
{
  "chapter": {
    "id": "chapter_глава-i-система-новейших-фундаментальных-открытий",
    "title": "Глава I. СИСТЕМА НОВЕЙШИХ ФУНДАМЕНТАЛЬНЫХ ОТКРЫТИЙ",
    "order": 1
  },
  "section": {
    "id": "chapter_глава-i-система-новейших-фундаментальных-открытий_9-фазовый-переход-высшего-рода",
    "title": "9 Фазовый Переход Высшего Рода",
    "number": "§ 14",
    "order": 14
  },
  "paragraphs": [
    {
      "id": "chapter_глава-i-система-новейших-фундаментальных-открытий_9-фазовый-переход-высшего-рода_p0",
      "content": "Как хорошо известно...",
      "order": 1,
      "tables": [],
      "illustrations": [],
      "formulas": [
        {
          "id": "af040a6115c8",
          "latex": "\\alpha",
          "wrapper_html": "<span>...</span>",
          "type": "inline"
        }
      ]
    }
  ],
  "metadata": {
    "previousChapter": null,
    "nextChapter": {
      "id": "chapter_глава-ii-основы-строения-твердого-тела",
      "title": "ГЛАВА II. ОСНОВЫ СТРОЕНИЯ ТВЕРДОГО ТЕЛА",
      "order": 2
    }
  }
}
```

## Структура ответа

### Chapter
- `id` (string) - Уникальный идентификатор главы
- `title` (string) - Название главы
- `order` (number) - Порядковый номер главы

### Section
- `id` (string) - Уникальный идентификатор секции
- `title` (string) - Название секции
- `number` (string, optional) - Номер секции (например, "§ 14")
- `order` (number) - Порядковый номер секции

### ParagraphWithReferences
- `id` (string) - Уникальный идентификатор абзаца
- `content` (string) - Содержимое абзаца
- `order` (number) - Порядковый номер абзаца в секции
- `tables` (TableReference[]) - Массив связанных таблиц
- `illustrations` (IllustrationReference[]) - Массив связанных иллюстраций
- `formulas` (FormulaReference[]) - Массив связанных формул

### TableReference
- `id` (string) - Уникальный идентификатор таблицы
- `content` (string) - HTML содержимое таблицы
- `html_attributes` (string, optional) - HTML атрибуты таблицы
- `type` (string, optional) - Тип таблицы

### IllustrationReference
- `id` (string) - Уникальный идентификатор иллюстрации
- `caption` (string, optional) - Подпись к иллюстрации
- `svg_content` (string, optional) - SVG содержимое
- `wrapper_html` (string, optional) - HTML обертка
- `type` (string, optional) - Тип иллюстрации

### FormulaReference
- `id` (string) - Уникальный идентификатор формулы
- `latex` (string) - LaTeX код формулы
- `wrapper_html` (string, optional) - HTML обертка
- `type` (string, optional) - Тип формулы (inline/display)

### Metadata
- `previousChapter` (ChapterMetadata | null) - Информация о предыдущей главе
- `nextChapter` (ChapterMetadata | null) - Информация о следующей главе

## Коды ответов

- `200 OK` - Успешный запрос
- `404 Not Found` - Абзац не найден или не связан с секцией
- `500 Internal Server Error` - Ошибка сервера

## Использование в Neo4j

Эндпоинт использует следующую структуру графа:

```cypher
(Chapter)-[:HAS_SECTION]->(Section)-[:HAS_PARAGRAPH]->(Paragraph)
(Paragraph)-[:CONTAINS_TABLE]->(Table)
(Paragraph)-[:CONTAINS_ILLUSTRATION]->(Illustration)
(Paragraph)-[:CONTAINS_FORMULA]->(Formula)
(Chapter)-[:PREVIOUS]->(Chapter)
(Chapter)-[:NEXT]->(Chapter)
```

## Примечания

- Абзацы возвращаются в порядке, определенном полем `order`
- Если глава первая, `previousChapter` будет `null`
- Если глава последняя, `nextChapter` будет `null`
- Пустые массивы для tables/illustrations/formulas означают отсутствие связей
