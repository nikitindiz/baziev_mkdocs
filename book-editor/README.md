# Book Editor - Интерактивная читалка книги Базиева

React приложение на Next.js для просмотра книги "Физика Базиева" с данными из Neo4j базы данных через REST API.

## 🚀 Возможности

- **📚 Интерактивное чтение** - просмотр всех параграфов книги с бесконечной прокруткой
- **🔗 Навигация** - переходы между параграфами через связи `previous`/`next`
- **⚡ TanStack Query** - кеширование и оптимизация запросов
- **🎨 Современный UI** - responsive дизайн с dark mode
- **📱 REST API** - полнофункциональный API для работы с параграфами
- **🔄 Автоподгрузка** - Intersection Observer для автоматической пагинации

## 📦 Технологии

- **Next.js 16** - React фреймворк с App Router
- **TanStack Query (React Query)** - управление серверным состоянием
- **Neo4j** - графовая база данных
- **TypeScript** - типизация
- **Tailwind CSS 4** - стилизация

## 🛠️ Установка

```bash
# Установка зависимостей
npm install

# Создание .env.local файла
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
```

## 🎯 Запуск

```bash
# Режим разработки
npm run dev

# Production build
npm run build
npm start
```

Приложение доступно: `http://localhost:3000`

## 📖 Структура

```
book-editor/
├── app/
│   ├── api/paragraphs/       # REST API
│   ├── reader/               # Читалка
│   └── providers.tsx         # React Query Provider
├── components/               # React компоненты
├── hooks/                    # Custom hooks
└── types/                    # TypeScript types
```

## 🎨 Страницы

- **`/`** - Главная
- **`/reader`** - Список параграфов (infinite scroll)
- **`/reader/:id`** - Просмотр параграфа
- **`/demo`** - API демо

## 🔌 API

### GET /api/paragraphs
```
?limit=20&cursor=xxx&section_id=xxx&chapter_id=xxx
```

### GET /api/paragraphs/:id
Получить параграф по ID

См. подробности в [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)

## 🎣 Hooks

```typescript
// Infinite scroll
const { data, fetchNextPage, hasNextPage } = useParagraphs(limit);

// Single paragraph
const { data } = useParagraph(id);
```

## 📄 Лицензия

MIT
