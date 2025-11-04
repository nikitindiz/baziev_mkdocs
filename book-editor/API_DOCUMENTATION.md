# Paragraphs API

REST API для работы с параграфами из Neo4j базы данных книги Базиева.

## Endpoints

### GET /api/paragraphs

Получить список параграфов с пагинацией.

#### Query Parameters

| Параметр | Тип | Обязательный | По умолчанию | Описание |
|----------|-----|--------------|--------------|----------|
| `limit` | number | Нет | 10 | Количество параграфов на страницу (1-100) |
| `cursor` | string | Нет | null | ID последнего параграфа с предыдущей страницы |
| `section_id` | string | Нет | null | Фильтр по ID секции |
| `chapter_id` | string | Нет | null | Фильтр по ID главы |

#### Response

```json
{
  "data": [
    {
      "id": "paragraph-id",
      "text": "Текст параграфа...",
      "order": 1,
      "section_id": "section-id",
      "chapter_id": "chapter-id",
      "previous": {
        "id": "prev-paragraph-id",
        "text": "Текст предыдущего параграфа..."
      },
      "next": {
        "id": "next-paragraph-id",
        "text": "Текст следующего параграфа..."
      }
    }
  ],
  "pagination": {
    "cursor": "last-paragraph-id",
    "hasMore": true,
    "total": 100
  }
}
```

#### Примеры использования

```bash
# Получить первые 10 параграфов
curl http://localhost:3000/api/paragraphs

# Получить следующие 20 параграфов
curl "http://localhost:3000/api/paragraphs?limit=20&cursor=paragraph-id"

# Фильтр по главе
curl "http://localhost:3000/api/paragraphs?chapter_id=chapter-1"

# Фильтр по секции с пагинацией
curl "http://localhost:3000/api/paragraphs?section_id=section-1&limit=15&cursor=paragraph-id"
```

---

### GET /api/paragraphs/:id

Получить конкретный параграф по ID.

#### Path Parameters

| Параметр | Тип | Описание |
|----------|-----|----------|
| `id` | string | ID параграфа |

#### Response

```json
{
  "id": "paragraph-id",
  "text": "Текст параграфа...",
  "order": 1,
  "section_id": "section-id",
  "chapter_id": "chapter-id",
  "previous": {
    "id": "prev-paragraph-id",
    "text": "Текст предыдущего параграфа..."
  },
  "next": {
    "id": "next-paragraph-id",
    "text": "Текст следующего параграфа..."
  }
}
```

#### Примеры использования

```bash
# Получить параграф по ID
curl http://localhost:3000/api/paragraphs/paragraph-id
```

---

## Типы данных

### Paragraph

```typescript
interface Paragraph {
  id: string;
  text: string;
  order?: number;
  section_id?: string;
  chapter_id?: string;
  previous?: {
    id: string;
    text: string;
  } | null;
  next?: {
    id: string;
    text: string;
  } | null;
}
```

### ParagraphsResponse

```typescript
interface ParagraphsResponse {
  data: Paragraph[];
  pagination: {
    cursor: string | null;  // ID последнего параграфа для следующего запроса
    hasMore: boolean;        // Есть ли еще параграфы
    total?: number;          // Общее количество (только в первом запросе)
  };
}
```

---

## Пагинация

API использует **cursor-based pagination** для эффективной навигации по большим наборам данных.

### Как работает пагинация

1. **Первый запрос**: не указывайте `cursor`
   ```bash
   GET /api/paragraphs?limit=10
   ```
   Ответ включает `total` (общее количество) и `cursor` (ID последнего элемента)

2. **Последующие запросы**: используйте `cursor` из предыдущего ответа
   ```bash
   GET /api/paragraphs?limit=10&cursor=last-id
   ```

3. **Проверка конца**: поле `hasMore` указывает, есть ли еще данные

### Пример полной навигации

```javascript
async function fetchAllParagraphs() {
  let cursor = null;
  let allParagraphs = [];
  
  do {
    const url = cursor 
      ? `/api/paragraphs?limit=20&cursor=${cursor}`
      : '/api/paragraphs?limit=20';
    
    const response = await fetch(url);
    const data = await response.json();
    
    allParagraphs.push(...data.data);
    cursor = data.pagination.cursor;
    
  } while (data.pagination.hasMore);
  
  return allParagraphs;
}
```

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Limit must be between 1 and 100"
}
```

### 404 Not Found
```json
{
  "error": "Paragraph not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Failed to fetch paragraphs"
}
```

---

## Конфигурация

Создайте файл `.env.local` в корне проекта:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

---

## Запуск

```bash
# Установка зависимостей
npm install

# Режим разработки
npm run dev

# Production build
npm run build
npm start
```

API будет доступен по адресу: `http://localhost:3000/api/paragraphs`
