Реализуй скрипт в папке `scripts` для создания базы данных для хранения блоков книги следующей структуры:

```sql
CREATE TABLE book_content (
    id SERIAL PRIMARY KEY,
    chapter_number VARCHAR(10),  -- "1", "10" и т.д.
    block_order INTEGER NOT NULL, -- глобальный порядковый номер
    block_type VARCHAR(50) NOT NULL, -- тип блока
    
    -- Текстовое содержимое
    text_content TEXT,
    
    -- Заголовки разных уровней
    header_level INTEGER, -- 1, 2, 3, 4
    header_content TEXT,
    
    -- Формулы
    formula_latex TEXT,
    formula_number VARCHAR(20), -- "(1.1)", "(10.2)" и т.д.
    is_inline BOOLEAN DEFAULT FALSE,
    
    -- Метаданные для формул и иллюстраций
    db_key VARCHAR(50),
    src_path TEXT,
    
    -- SVG иллюстрации
    svg_content TEXT,
    illustration_caption TEXT,
    
    -- Таблицы
    table_html TEXT,
    
    -- Форматирование
    starts_new_paragraph BOOLEAN DEFAULT FALSE,
    
    -- Дополнительные метаданные
    parent_section_id INTEGER REFERENCES book_content(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для быстрого поиска
CREATE INDEX idx_chapter ON book_content(chapter_number);
CREATE INDEX idx_block_order ON book_content(block_order);
CREATE INDEX idx_block_type ON book_content(block_type);
CREATE INDEX idx_formula_number ON book_content(formula_number);
```

Используй SQLite для реализации базы данных. Скрипт должен создавать базу данных и таблицу с указанной структурой, а также необходимые индексы для оптимизации запросов.