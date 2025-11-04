# Book Editor - Краткое руководство

## 🎯 Быстрый старт

```bash
# 1. Установка
npm install

# 2. Настройка .env.local
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=20021030
NEO4J_DATABASE=neo4j

# 3. Запуск
npm run dev
```

Открыть: `http://localhost:3000`

## 📱 Основные возможности

### 1. Читалка книги (`/reader`)
- Бесконечная прокрутка параграфов
- Автоматическая подгрузка при скролле
- Настройка количества параграфов на странице
- Статистика загруженных параграфов

### 2. Просмотр параграфа (`/reader/:id`)
- Детальный просмотр параграфа
- Навигация к предыдущему/следующему
- Метаданные (глава, секция, порядок)
- Быстрые переходы

### 3. REST API
```bash
# Получить параграфы
curl "http://localhost:3000/api/paragraphs?limit=10"

# С пагинацией
curl "http://localhost:3000/api/paragraphs?limit=10&cursor=xxx"

# Конкретный параграф
curl "http://localhost:3000/api/paragraphs/:id"
```

## 🔧 Технический стек

| Технология | Назначение |
|------------|------------|
| Next.js 16 | React фреймворк |
| TanStack Query | Управление данными |
| Neo4j | База данных |
| TypeScript | Типизация |
| Tailwind CSS | Стилизация |

## 📊 Данные

- **Всего параграфов**: 6921
- **Иллюстрации**: 69
- **Источник**: Neo4j графовая БД
- **Связи**: Previous/Next навигация

## 🎨 Компоненты

### ParagraphCard
```tsx
<ParagraphCard 
  paragraph={data} 
  index={0}
  showNavigation={true}
/>
```

### ParagraphsList
```tsx
<ParagraphsList 
  limit={20}
  sectionId="xxx"
  chapterId="xxx"
/>
```

## 🎣 React Hooks

### useParagraphs (infinite scroll)
```typescript
const {
  data,              // { pages, paragraphs, total }
  fetchNextPage,     // загрузить еще
  hasNextPage,       // есть ли еще
  isFetchingNextPage // загрузка в процессе
} = useParagraphs(20);
```

### useParagraph (single item)
```typescript
const {
  data,      // Paragraph
  isLoading,
  isError
} = useParagraph(id);
```

## 🚀 Деплой

```bash
npm run build
npm start
```

## 📖 Документация

- [API Documentation](./API_DOCUMENTATION.md) - REST API
- [README.md](./README.md) - Полное описание

## ⚡ Features

✅ Cursor-based pagination  
✅ Infinite scroll  
✅ Auto-loading  
✅ Dark mode  
✅ Responsive design  
✅ TypeScript  
✅ React Query caching  
✅ Neo4j integration  

## 🔗 Полезные ссылки

- Главная: `http://localhost:3000/`
- Читалка: `http://localhost:3000/reader`
- API Demo: `http://localhost:3000/demo`
- API Docs: `http://localhost:3000/API_DOCUMENTATION.md`
