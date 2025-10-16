Реализуй скрипт для парсинга markdown-файлов книги и сохранения блоков в базу данных.

База данных уже существует, структура таблицы следующая:
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

Пример алгоритма парсинга:
```python
import re
from typing import List, Dict, Any
import json

class BookParser:
    def __init__(self):
        self.blocks = []
        self.block_order = 0
        self.current_chapter = None
        
    def parse_document(self, markdown_content: str) -> List[Dict[str, Any]]:
        lines = markdown_content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Пропускаем пустые строки
            if not line:
                i += 1
                continue
            
            # Проверяем заголовки
            if line.startswith('##'):
                self._add_header_block(line)
                i += 1
                continue
            
            # Проверяем отдельные формулы
            if line.startswith('<div style="display: flex'):
                formula_block = self._extract_formula_block(lines, i)
                self._add_formula_block(formula_block)
                i = formula_block['end_line']
                continue
            
            # Проверяем SVG иллюстрации
            if '<svg' in line or 'data-db-key' in line and 'illustration' in lines[i-1] if i > 0 else False:
                svg_block = self._extract_svg_block(lines, i)
                self._add_svg_block(svg_block)
                i = svg_block['end_line']
                continue
            
            # Проверяем таблицы
            if line.startswith('<table'):
                table_block = self._extract_table_block(lines, i)
                self._add_table_block(table_block)
                i = table_block['end_line']
                continue
            
            # Обрабатываем обычный текст с возможными inline формулами
            self._process_text_line(line)
            i += 1
            
        return self.blocks
    
    def _add_header_block(self, line: str):
        level = len(re.match(r'^#+', line).group())
        content = line.lstrip('#').strip()
        
        # Извлекаем номер главы/параграфа
        chapter_match = re.match(r'§\s*(\d+)', content)
        if chapter_match:
            self.current_chapter = chapter_match.group(1)
        
        self.blocks.append({
            'block_order': self._get_next_order(),
            'block_type': 'header',
            'header_level': level - 1,  # Приводим к 1-4
            'header_content': content,
            'chapter_number': self.current_chapter,
            'starts_new_paragraph': True
        })
    
    def _process_text_line(self, line: str):
        # Разделяем текст на части с формулами и без
        parts = re.split(r'(<span[^>]*data-db-key[^>]*>.*?</span>)', line)
        
        for part in parts:
            if not part.strip():
                continue
                
            if 'data-db-key' in part:
                # Это inline формула
                self._add_inline_formula(part)
            else:
                # Обычный текст
                self._add_text_block(part)
    
    def _add_inline_formula(self, formula_html: str):
        # Извлекаем LaTeX и метаданные
        latex_match = re.search(r'\$([^$]+)\$', formula_html)
        db_key_match = re.search(r'data-db-key="([^"]+)"', formula_html)
        src_match = re.search(r'data-src="([^"]+)"', formula_html)
        
        self.blocks.append({
            'block_order': self._get_next_order(),
            'block_type': 'inline_formula',
            'formula_latex': latex_match.group(1) if latex_match else None,
            'db_key': db_key_match.group(1) if db_key_match else None,
            'src_path': src_match.group(1) if src_match else None,
            'is_inline': True,
            'chapter_number': self.current_chapter,
            'starts_new_paragraph': False
        })
    
    def _add_formula_block(self, formula_data: Dict):
        # Извлекаем LaTeX формулу и номер
        latex = formula_data.get('latex', '')
        number = formula_data.get('number', '')
        
        self.blocks.append({
            'block_order': self._get_next_order(),
            'block_type': 'standalone_formula',
            'formula_latex': latex,
            'formula_number': number,
            'db_key': formula_data.get('db_key'),
            'src_path': formula_data.get('src'),
            'is_inline': False,
            'chapter_number': self.current_chapter,
            'starts_new_paragraph': True
        })
    
    def _add_text_block(self, text: str):
        if not text.strip():
            return
            
        self.blocks.append({
            'block_order': self._get_next_order(),
            'block_type': 'text',
            'text_content': text.strip(),
            'chapter_number': self.current_chapter,
            'starts_new_paragraph': text[0].isupper() or text.startswith('«')
        })
    
    def _extract_formula_block(self, lines: List[str], start_idx: int) -> Dict:
        # Логика извлечения блока формулы
        result = {'start_line': start_idx}
        latex_lines = []
        
        for i in range(start_idx, min(start_idx + 20, len(lines))):
            line = lines[i]
            
            # Ищем LaTeX между $$
            if '$$' in line:
                latex_lines.append(line)
                if latex_lines and line.strip().endswith('$$'):
                    break
            
            # Ищем номер формулы
            if re.search(r'\(\d+\.\d+\)', line):
                result['number'] = re.search(r'\((\d+\.\d+)\)', line).group(1)
            
            # Ищем метаданные
            if 'data-db-key' in line:
                result['db_key'] = re.search(r'data-db-key="([^"]+)"', line).group(1)
            if 'data-src' in line:
                result['src'] = re.search(r'data-src="([^"]+)"', line).group(1)
            
            if '</div>' in line and i > start_idx:
                result['end_line'] = i + 1
                break
        
        # Собираем LaTeX
        latex_text = ' '.join(latex_lines)
        latex_match = re.search(r'\$\$(.*?)\$\$', latex_text, re.DOTALL)
        if latex_match:
            result['latex'] = latex_match.group(1).strip()
        
        return result
    
    def _get_next_order(self) -> int:
        self.block_order += 1
        return self.block_order
```

Пример использования:
```python
# Чтение и парсинг документа
with open('chapter1.md', 'r', encoding='utf-8') as f:
    content = f.read()

parser = BookParser()
blocks = parser.parse_document(content)

# Сохранение в БД
import psycopg2

conn = psycopg2.connect(...)
cur = conn.cursor()

for block in blocks:
    cur.execute("""
        INSERT INTO book_content 
        (block_order, block_type, chapter_number, text_content, 
         header_level, header_content, formula_latex, formula_number,
         is_inline, db_key, src_path, svg_content, illustration_caption,
         table_html, starts_new_paragraph)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        block.get('block_order'),
        block.get('block_type'),
        block.get('chapter_number'),
        block.get('text_content'),
        block.get('header_level'),
        block.get('header_content'),
        block.get('formula_latex'),
        block.get('formula_number'),
        block.get('is_inline'),
        block.get('db_key'),
        block.get('src_path'),
        block.get('svg_content'),
        block.get('illustration_caption'),
        block.get('table_html'),
        block.get('starts_new_paragraph')
    ))

conn.commit()
```
