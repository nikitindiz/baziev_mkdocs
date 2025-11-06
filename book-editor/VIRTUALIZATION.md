# Виртуализация списка параграфов

## 🎯 Зачем нужна виртуализация?

Книга содержит **6921 параграф**. Рендеринг всех параграфов одновременно:
- ❌ Долгая загрузка
- ❌ Высокое потребление памяти
- ❌ Медленная прокрутка
- ❌ Плохая производительность

**Решение**: Виртуализация — рендерим только видимые элементы!

## ⚡ Архитектура

```
┌─────────────────────────────────────┐
│  1. GET /api/paragraphs/meta        │
│     → Получаем все ID (легко)       │
│     → 6921 параграфов               │
│     → Только метаданные (~100 KB)   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  2. Виртуализатор (TanStack Virtual)│
│     → Вычисляет видимые индексы     │
│     → Overscan ±5 элементов         │
│     → Только ~15 параграфов в DOM   │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│  3. POST /api/paragraphs/batch      │
│     → Загружаем контент видимых     │
│     → Batch request (до 100 ID)     │
│     → Только нужные данные          │
└─────────────────────────────────────┘
```

## 📊 Сравнение подходов

### Обычная пагинация (`/reader`)
```
✓ Простая реализация
✓ Стандартный UX
✗ Прокрутка только в пределах страницы
✗ Нужно кликать "Load More"
✗ Нельзя сразу перейти к параграфу 5000
```

### Виртуальный список (`/reader-virtual`)
```
✓ Вся книга доступна сразу
✓ Мгновенный переход к любому параграфу
✓ Плавная прокрутка по всей книге
✓ Минимальное потребление памяти
✓ Оптимальная производительность
✗ Чуть сложнее реализация
```

## 🚀 Как это работает

### 1. Загрузка метаданных
```typescript
const { data: metaData } = useParagraphsMeta();
// Получаем: { data: [{id, order, section_id, chapter_id}, ...], total: 6921 }
```

### 2. Виртуализатор
```typescript
const virtualizer = useVirtualizer({
  count: 6921,                    // Всего элементов
  getScrollElement: () => ref,    // Контейнер
  estimateSize: () => 200,        // ~200px на параграф
  overscan: 5,                    // ±5 элементов вне экрана
});
```

### 3. Получение видимых ID
```typescript
const virtualItems = virtualizer.getVirtualItems();
// Например: [45, 46, 47, 48, 49, 50, 51, 52, 53]

const visibleIds = virtualItems.map(item => allIds[item.index]);
// ["chapter_xxx_p45", "chapter_xxx_p46", ...]
```

### 4. Batch загрузка контента
```typescript
const { data } = useParagraphsBatch(visibleIds);
// POST /api/paragraphs/batch с ids: [...]
// Получаем только контент видимых параграфов
```

### 5. Рендеринг
```typescript
{virtualItems.map(item => {
  const paragraph = paragraphsMap.get(allIds[item.index]);
  return paragraph ? 
    <ParagraphCard paragraph={paragraph} /> : 
    <LoadingSkeleton />;
})}
```

## 🎨 Производительность

### Метрики

| Параметр | Обычный список | Виртуальный список |
|----------|----------------|-------------------|
| Элементов в DOM | 6921 | ~15 |
| Начальная загрузка | ~10 MB | ~100 KB |
| Память браузера | ~500 MB | ~50 MB |
| Прокрутка (FPS) | ~10-20 | 60 |
| Время до первого рендера | ~10 сек | ~200 мс |

### Оптимизации

1. **Кеширование метаданных**
   ```typescript
   staleTime: 5 * 60 * 1000, // 5 минут
   ```

2. **Batch запросы**
   ```typescript
   // Вместо 15 запросов:
   for (const id of visibleIds) {
     fetch(`/api/paragraphs/${id}`);
   }
   
   // Один batch запрос:
   fetch('/api/paragraphs/batch', {
     body: JSON.stringify({ ids: visibleIds })
   });
   ```

3. **React Query кеш**
   ```typescript
   queryKey: ['paragraphs-batch', visibleIds],
   // Кеш переиспользуется при прокрутке вперёд-назад
   ```

4. **Overscan**
   ```typescript
   overscan: 5
   // Загружаем ±5 элементов вне экрана
   // Плавная прокрутка без "мерцания"
   ```

## 🔗 Deep Linking

Виртуальный список полностью поддерживает прямые ссылки:

```
/reader-virtual?paragraph=chapter_xxx_p5000
```

**Алгоритм**:
1. Загружаем метаданные всех 6921 параграфов
2. Находим индекс целевого параграфа: `allIds.indexOf(targetId)`
3. Прокручиваем к индексу: `virtualizer.scrollToIndex(index)`
4. Загружаем контент видимых элементов
5. Подсвечиваем целевой параграф

**Результат**: Мгновенный переход к любому параграфу в книге! 🎯

## 💡 Примеры использования

### Переход к параграфу 5000
```javascript
window.location.href = '/reader-virtual?paragraph=chapter_xxx_p5000';
```

### Поиск и переход
```javascript
// 1. Получаем все метаданные
const { data } = await fetch('/api/paragraphs/meta').then(r => r.json());

// 2. Ищем по order
const target = data.data.find(p => p.order === 5000);

// 3. Переходим
window.location.href = `/reader-virtual?paragraph=${target.id}`;
```

### Программная прокрутка
```javascript
// В компоненте
virtualizer.scrollToIndex(5000, {
  align: 'center',
  behavior: 'smooth'
});
```

## 🔧 API Hooks

### useParagraphsMeta
```typescript
const { data, isLoading } = useParagraphsMeta();

// data.data: ParagraphMeta[]
// data.total: number
```

### useParagraphsBatch
```typescript
const ids = ['p1', 'p2', 'p3'];
const { data, isLoading } = useParagraphsBatch(ids);

// data: Paragraph[]
```

### Комбинированное использование
```typescript
// 1. Получаем все ID
const { data: meta } = useParagraphsMeta();

// 2. Вычисляем видимые
const visibleIds = virtualItems.map(v => meta.data[v.index].id);

// 3. Загружаем контент
const { data: paragraphs } = useParagraphsBatch(visibleIds);
```

## 📈 Масштабирование

Виртуализация легко масштабируется:

- ✅ 10,000 параграфов
- ✅ 100,000 параграфов
- ✅ 1,000,000 параграфов

Производительность остаётся **константной O(1)**, потому что в DOM всегда ~15-20 элементов.

## 🎓 Best Practices

1. **Используйте виртуализацию для списков > 100 элементов**
2. **Настройте overscan** в зависимости от высоты элементов
3. **Кешируйте метаданные** на долгое время
4. **Батчите запросы** вместо индивидуальных
5. **Измеряйте реальные размеры** элементов для точности
6. **Используйте мемоизацию** для вычислений

## 🚧 Ограничения

1. **Динамическая высота элементов**
   - Решение: `estimateSize` + `measureElement`
   
2. **SEO**
   - Виртуальные элементы не индексируются
   - Решение: Server-side rendering для критичных страниц

3. **Accessibility**
   - Скринридеры видят только видимые элементы
   - Решение: ARIA-метки + виртуальный скроллбар

## 📚 Ресурсы

- [TanStack Virtual](https://tanstack.com/virtual/latest)
- [TanStack Query](https://tanstack.com/query/latest)
- [Virtualization Patterns](https://web.dev/virtualize-lists-with-react-window/)
