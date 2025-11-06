# Inline Formula Rendering - Update

## Что было добавлено

Поддержка рендеринга inline формул в тексте абзацев с использованием KaTeX.

## Изменения

### 1. Установлены пакеты
```bash
npm install katex react-katex
```

### 2. Подключен CSS KaTeX
**File**: `/app/layout.tsx`
```typescript
import "katex/dist/katex.min.css";
```

### 3. Создана утилита для рендеринга LaTeX
**File**: `/lib/latex-renderer.ts`

Функции:
- `renderLatex(latex, displayMode)` - рендерит LaTeX в HTML с помощью KaTeX
- `replaceFormulaPlaceholders(content, formulas)` - заменяет `{{formula:id}}` на рендеренный LaTeX

### 4. Обновлен компонент Paragraph
**File**: `/app/read-in-context/components/Paragraph.tsx`

**Inline формулы** (в тексте):
- Плейсхолдеры `{{formula:id}}` автоматически заменяются на inline LaTeX
- Рендерятся с `displayMode: false`

**Block формулы** (отдельно):
- Рендерятся с `displayMode: true` (центрированные, крупнее)
- Остаются в секции "Formulas" внизу абзаца

## Как это работает

### До
```html
Классическая молекулярная физика основывается на том, 
что кинетическую энергию молекул газов можно описать 
двумя способами: механически {{formula:554a691a7db4}} 
и термодинамически {{formula:3aa4dd43831a}}.
```

### После (в браузере)
```html
Классическая молекулярная физика основывается на том, 
что кинетическую энергию молекул газов можно описать 
двумя способами: механически <span class="katex">E = mv²/2</span>
и термодинамически <span class="katex">E = 3kT/2</span>.
```

## Пример данных

### Абзац с inline формулами
```json
{
  "id": "chapter_..._p7",
  "content": "...механически {{formula:554a691a7db4}} и термодинамически {{formula:3aa4dd43831a}}...",
  "formulas": [
    {
      "id": "554a691a7db4",
      "latex": "E = mv^2/2",
      "type": "inline"
    },
    {
      "id": "3aa4dd43831a",
      "latex": "E = 3kT/2",
      "type": "inline"
    }
  ]
}
```

## Алгоритм замены

1. Получаем content абзаца
2. Создаем Map: `formulaId → latex`
3. Используем regex `/\{\{formula:([a-f0-9]+)\}\}/g`
4. Для каждого match:
   - Извлекаем formulaId
   - Находим latex в Map
   - Рендерим через KaTeX
   - Заменяем placeholder на HTML

## Props компонента

```typescript
interface ParagraphProps {
  paragraph: ParagraphWithReferences;
  isTarget?: boolean;
  renderFormulas?: boolean;  // по умолчанию true
}
```

Если `renderFormulas = false`, плейсхолдеры не заменяются.

## Обработка ошибок

- Если формула не найдена в массиве: показывается оранжевый placeholder с title
- Если LaTeX некорректный: KaTeX возвращает error span (красный текст)
- `throwOnError: false` - не ломает рендеринг при ошибке в формуле

## Производительность

- Regex замена выполняется один раз при рендере компонента
- Map для формул создается один раз
- KaTeX рендерит на стороне сервера (SSR-friendly)

## Статус

✅ KaTeX установлен  
✅ CSS подключен  
✅ Утилита создана  
✅ Компонент обновлен  
✅ Inline формулы рендерятся  
✅ Block формулы рендерятся  
✅ Обработка ошибок реализована  

## Готово! 🎉
