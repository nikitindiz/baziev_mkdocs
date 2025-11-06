# Symbol Formula Highlighting - Update

## Что было добавлено

Визуальное выделение формул-символов с высокой уверенностью распознавания и tooltip с определениями.

## Изменения

### 1. Обновлены типы
**File**: `/types/paragraph-context.ts`

Добавлены поля в `FormulaReference`:
```typescript
interface FormulaReference {
  id: string;
  latex: string;
  wrapper_html?: string;
  type?: string;
  is_symbol?: boolean;                    // ← НОВОЕ
  symbol_parse_confidence?: string;       // ← НОВОЕ: "high", "med", "low"
  symbol_definition?: string;             // ← НОВОЕ
}
```

### 2. Обновлен API
**File**: `/app/api/paragraphs/[id]/context/route.ts`

Cypher запрос теперь возвращает дополнительные поля:
```cypher
collect(DISTINCT {
  id: f.id,
  latex: f.latex,
  wrapper_html: f.wrapper_html,
  type: f.type,
  is_symbol: f.is_symbol,
  symbol_parse_confidence: f.symbol_parse_confidence,
  symbol_definition: f.symbol_definition
}) as formulas
```

### 3. Обновлена утилита рендеринга
**File**: `/lib/latex-renderer.ts`

Функция `replaceFormulaPlaceholders` теперь:
1. Проверяет `is_symbol === true` && `symbol_parse_confidence === "high"`
2. Если условие выполнено, оборачивает формулу в `<span class="symbol-formula" data-tooltip="...">`
3. Экранирует HTML в tooltip через `escapeHtml()`

### 4. Добавлены стили
**File**: `/app/globals.css`

```css
.symbol-formula {
  border: 2px solid #10b981;  /* зеленая обводка */
  cursor: help;
}

.symbol-formula:hover {
  background-color: #d1fae5;  /* светло-зеленый фон */
}

.symbol-formula::after {
  /* Tooltip с определением */
  content: attr(data-tooltip);
  position: absolute;
  bottom: 100%;
  /* ... стили tooltip */
}
```

## Как это работает

### Условие подсветки
Формула выделяется зеленой обводкой ТОЛЬКО если:
```typescript
formula.is_symbol === true && 
formula.symbol_parse_confidence === "high"
```

### До (в HTML)
```html
механически {{formula:554a691a7db4}} и {{formula:86b054bbb0a5}}
```

### После (в браузере)
```html
механически <span class="katex">E = mv²/2</span> и 
<span class="symbol-formula" data-tooltip="Постоянная Больцмана...">
  <span class="katex">k</span>
</span>
```

## Визуальные эффекты

### Обычная формула
- Без обводки
- Просто отрендеренный LaTeX

### Символ (high confidence)
- ✅ Зеленая обводка 2px
- ✅ Курсор `help` (вопросительный знак)
- ✅ При наведении: светло-зеленый фон
- ✅ При наведении: появляется tooltip с определением

### Символ (med/low confidence)
- Без обводки (отображается как обычная формула)

## Пример данных

```json
{
  "id": "86b054bbb0a5",
  "latex": "k",
  "is_symbol": true,
  "symbol_parse_confidence": "high",
  "symbol_definition": "Постоянная Больцмана — фундаментальная физическая константа..."
}
```

## Tooltip

- Появляется сверху от формулы
- Максимальная ширина: 300px
- Темно-серый фон (#1f2937)
- Белый текст
- Стрелка указывает на формулу
- Плавное появление/исчезновение (0.2s)
- Поддерживает темную тему

## Темная тема

В темной теме:
- Tooltip: серый фон (#374151)
- Hover фон: темно-зеленый (#064e3b)
- Обводка остается зеленой

## Безопасность

HTML в определениях экранируется через `escapeHtml()`:
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&#039;`
- `&` → `&amp;`

## Производительность

- Проверка условий выполняется один раз при замене placeholder
- CSS transitions используют GPU acceleration
- Tooltip рендерится через CSS `::after` (без DOM элементов)

## Пример в тексте

**Исходный текст:**
```
Классическая молекулярная физика основывается на том, что кинетическую 
энергию молекул газов можно описать двумя способами: механически 
{{formula:554a691a7db4}} и термодинамически {{formula:3aa4dd43831a}}.
```

**В браузере:**
- `E = mv²/2` - обычная формула (это уравнение, не символ)
- `E = 3kT/2` - обычная формула (это уравнение, не символ)
- Но если в тексте есть отдельные `k` или `T`, они будут с зеленой обводкой

## Критерии выделения

| is_symbol | confidence | Обводка | Tooltip |
|-----------|------------|---------|---------|
| true      | high       | ✅ Да   | ✅ Да   |
| true      | med        | ❌ Нет  | ❌ Нет  |
| true      | low        | ❌ Нет  | ❌ Нет  |
| false/null| any        | ❌ Нет  | ❌ Нет  |

## Статус

✅ Типы обновлены  
✅ API расширен  
✅ Утилита рендеринга обновлена  
✅ CSS стили добавлены  
✅ Tooltip реализован  
✅ Темная тема поддерживается  
✅ HTML экранирование работает  
✅ Условия подсветки реализованы  

## Готово! 🎉

Теперь символы с высокой уверенностью распознавания выделяются зеленой обводкой, 
а при наведении показывается их определение!
