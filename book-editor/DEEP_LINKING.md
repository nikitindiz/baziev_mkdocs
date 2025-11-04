# Примеры использования Book Editor

## 🔗 Прямые ссылки на параграфы

### Базовое использование

Чтобы открыть страницу читалки и автоматически прокрутить к конкретному параграфу, используйте query параметр `paragraph`:

```
http://localhost:3000/reader?paragraph=<paragraph-id>
```

### Примеры

1. **Параграф из главы I:**
```
http://localhost:3000/reader?paragraph=chapter_глава-i-система-новейших-фундаментальных-открытий_1-гиперчастотная-механика-или-механика-микромира_p13
```

2. **С URL encoding:**
```
http://localhost:3000/reader?paragraph=chapter_%D0%B3%D0%BB%D0%B0%D0%B2%D0%B0-i-%D1%81%D0%B8%D1%81%D1%82%D0%B5%D0%BC%D0%B0-%D0%BD%D0%BE%D0%B2%D0%B5%D0%B9%D1%88%D0%B8%D1%85-%D1%84%D1%83%D0%BD%D0%B4%D0%B0%D0%BC%D0%B5%D0%BD%D1%82%D0%B0%D0%BB%D1%8C%D0%BD%D1%8B%D1%85-%D0%BE%D1%82%D0%BA%D1%80%D1%8B%D1%82%D0%B8%D0%B9_1-%D0%B3%D0%B8%D0%BF%D0%B5%D1%80%D1%87%D0%B0%D1%81%D1%82%D0%BE%D1%82%D0%BD%D0%B0%D1%8F-%D0%BC%D0%B5%D1%85%D0%B0%D0%BD%D0%B8%D0%BA%D0%B0-%D0%B8%D0%BB%D0%B8-%D0%BC%D0%B5%D1%85%D0%B0%D0%BD%D0%B8%D0%BA%D0%B0-%D0%BC%D0%B8%D0%BA%D1%80%D0%BE%D0%BC%D0%B8%D1%80%D0%B0_p13
```

## 🎯 Как это работает

### 1. Автоматическая прокрутка
- При загрузке страницы с параметром `paragraph`, приложение:
  - Загружает первые N параграфов
  - Проверяет наличие целевого параграфа
  - Если параграф не найден, автоматически загружает следующую порцию
  - Повторяет до тех пор, пока не найдет целевой параграф
  - Прокручивает страницу к параграфу с плавной анимацией

### 2. Визуальная подсветка
- Целевой параграф подсвечивается на 3 секунды
- Добавляется синяя левая граница
- Анимация затухания фона

### 3. Копирование ссылок
- В каждой карточке параграфа есть кнопка "🔗 Ссылка"
- Клик копирует полную URL-ссылку в буфер обмена
- Можно делиться конкретными параграфами с другими пользователями

## 📱 Использование в UI

### Кнопка копирования
```tsx
// В каждой карточке параграфа
<button onClick={copyLink}>
  {copied ? '✓ Скопировано' : '🔗 Ссылка'}
</button>
```

### Программное создание ссылки
```javascript
const createParagraphLink = (paragraphId) => {
  return `${window.location.origin}/reader?paragraph=${encodeURIComponent(paragraphId)}`;
};
```

## 🎨 Стилизация подсветки

Целевой параграф получает класс `highlight-paragraph` с анимацией:

```css
@keyframes highlight {
  0% { background-color: rgba(59, 130, 246, 0.3); }
  100% { background-color: transparent; }
}

.highlight-paragraph {
  animation: highlight 3s ease-out;
  border-left: 4px solid rgb(59, 130, 246) !important;
}
```

## 🔧 API Integration

### Получить ID параграфа
```bash
# Список параграфов
curl "http://localhost:3000/api/paragraphs?limit=10"

# Ответ содержит ID каждого параграфа
{
  "data": [
    { "id": "chapter_xxx_p13", ... }
  ]
}
```

### Создать ссылку программно
```javascript
fetch('/api/paragraphs?limit=1')
  .then(res => res.json())
  .then(data => {
    const firstParagraph = data.data[0];
    const link = `/reader?paragraph=${encodeURIComponent(firstParagraph.id)}`;
    console.log(link);
  });
```

## 💡 Примеры использования

### Создание оглавления с прямыми ссылками
```jsx
const TableOfContents = ({ paragraphs }) => (
  <nav>
    {paragraphs.map(p => (
      <a href={`/reader?paragraph=${encodeURIComponent(p.id)}`}>
        {p.title || p.id}
      </a>
    ))}
  </nav>
);
```

### Навигация из внешнего источника
```html
<!-- Email или документ -->
<a href="http://your-domain.com/reader?paragraph=chapter_xxx_p13">
  Перейти к параграфу 13
</a>
```

### Сохранение позиции чтения
```javascript
// Сохранить текущий параграф
const saveReadingPosition = (paragraphId) => {
  localStorage.setItem('lastReadParagraph', paragraphId);
};

// Восстановить позицию
const restoreReadingPosition = () => {
  const lastParagraph = localStorage.getItem('lastReadParagraph');
  if (lastParagraph) {
    window.location.href = `/reader?paragraph=${encodeURIComponent(lastParagraph)}`;
  }
};
```

## 🚀 Расширенные возможности

### Комбинирование с фильтрами (будущая функция)
```
/reader?paragraph=xxx&chapter=глава-i&section=механика
```

### Deep linking из других приложений
```javascript
// React Native / Mobile app
Linking.openURL('yourapp://reader?paragraph=xxx');
```

### Создание постоянных закладок
```javascript
const bookmarks = [
  { name: 'Важная формула', paragraphId: 'chapter_xxx_p13' },
  { name: 'Эксперимент', paragraphId: 'chapter_yyy_p42' }
];

// Генерация ссылок
bookmarks.map(b => ({
  ...b,
  url: `/reader?paragraph=${encodeURIComponent(b.paragraphId)}`
}));
```

## 📊 Метрики и аналитика

```javascript
// Отслеживание переходов по прямым ссылкам
useEffect(() => {
  const targetId = searchParams.get('paragraph');
  if (targetId) {
    analytics.track('paragraph_deep_link', {
      paragraphId: targetId,
      timestamp: new Date()
    });
  }
}, []);
```

## ✅ Best Practices

1. **Всегда используйте encodeURIComponent** для кириллических ID
2. **Проверяйте существование параграфа** перед созданием ссылки
3. **Добавляйте fallback** на случай если параграф не найден
4. **Используйте короткие алиасы** для часто используемых параграфов
5. **Кешируйте ссылки** для улучшения производительности
