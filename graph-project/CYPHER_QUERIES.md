# Полезные Cypher запросы для работы с графом

## Просмотр структуры

### 1. Все главы книги
```cypher
MATCH (b:Book)-[:HAS_CHAPTER]->(ch:Chapter)
RETURN b.title as book, ch.order, ch.title
ORDER BY ch.order
```

### 2. Все секции главы
```cypher
MATCH (ch:Chapter {title: "Глава I. СИСТЕМА НОВЕЙШИХ ФУНДАМЕНТАЛЬНЫХ ОТКРЫТИЙ"})-[:HAS_SECTION]->(s:Section)
RETURN s.order, s.number, s.title
ORDER BY s.order
```

### 3. Параграфы секции с навигацией
```cypher
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
WHERE s.id STARTS WITH "chapter_глава-i-система-новейших"
OPTIONAL MATCH (p)-[:NEXT]->(next:Paragraph)
OPTIONAL MATCH (prev:Paragraph)-[:NEXT]->(p)
RETURN p.order, 
       left(p.content, 100) + '...' as content_preview,
       prev.order as prev_order,
       next.order as next_order
ORDER BY p.order
LIMIT 20
```

## Навигация по последовательности

### 4. Путь через все параграфы секции
```cypher
MATCH path = (s:Section {id: "chapter_глава-i-система-новейших-фундаментальных-открытий_section-1-вселенная-как-объект-научного-исследования"})-[:HAS_PARAGRAPH]->(first:Paragraph)
WHERE NOT exists((first)<-[:NEXT]-())
MATCH chain = (first)-[:NEXT*0..10]->(p:Paragraph)
RETURN p.order, left(p.content, 80) as preview
ORDER BY p.order
```

### 5. Следующие 5 параграфов после текущего
```cypher
MATCH (p:Paragraph {id: "chapter_глава-i-система-новейших-фундаментальных-открытий_section-1-вселенная-как-объект-научного-исследования_p0"})
MATCH path = (p)-[:NEXT*1..5]->(next:Paragraph)
RETURN next.order, left(next.content, 100) as preview
ORDER BY length(path)
```

### 6. Предыдущие параграфы
```cypher
MATCH (p:Paragraph {id: "chapter_глава-i-система-новейших-фундаментальных-открытий_section-1-вселенная-как-объект-научного-исследования_p5"})
MATCH path = (prev:Paragraph)-[:NEXT*1..5]->(p)
RETURN prev.order, left(prev.content, 100) as preview
ORDER BY length(path) DESC
```

### 7. Цепочка секций в главе
```cypher
MATCH (ch:Chapter {id: "chapter_глава-i-система-новейших-фундаментальных-открытий"})-[:HAS_SECTION]->(first:Section)
WHERE NOT exists((first)<-[:NEXT]-())
MATCH path = (first)-[:NEXT*0..]->(s:Section)
RETURN s.order, s.number, s.title
ORDER BY s.order
```

## Контент и связи

### 8. Параграфы с формулами
```cypher
MATCH (p:Paragraph)-[r:CONTAINS_FORMULA]->(f:Formula)
RETURN p.id, 
       left(p.content, 100) as content_preview,
       f.latex,
       r.position
ORDER BY p.order
LIMIT 20
```

### 9. Параграфы с цитатами литературы
```cypher
MATCH (p:Paragraph)-[:CITES]->(l:Literature)
RETURN p.id,
       left(p.content, 100) as content_preview,
       l.number,
       l.author,
       l.title
ORDER BY p.order
LIMIT 20
```

### 10. Статистика по секции
```cypher
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
WITH s, count(p) as para_count, sum(p.word_count) as total_words
OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p2)-[:CONTAINS_FORMULA]->(f:Formula)
WITH s, para_count, total_words, count(DISTINCT f) as formula_count
OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p3)-[:CITES]->(l:Literature)
WITH s, para_count, total_words, formula_count, count(DISTINCT l) as citation_count
RETURN s.number, 
       s.title, 
       para_count, 
       total_words,
       formula_count,
       citation_count
ORDER BY s.order
```

## Визуализация

### 11. Граф структуры главы (ограниченный)
```cypher
MATCH path = (ch:Chapter {id: "chapter_глава-i-система-новейших-фундаментальных-открытий"})-[:HAS_SECTION]->(s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
WHERE p.order <= 3
RETURN path
LIMIT 50
```

### 12. Граф с формулами и символами
```cypher
MATCH (p:Paragraph {id: "chapter_глава-i-система-новейших-фундаментальных-открытий_section-1-вселенная-как-объект-научного-исследования_p0"})
OPTIONAL MATCH path1 = (p)-[:CONTAINS_FORMULA]->(f:Formula)-[:USES_SYMBOL]->(sym:Symbol)
OPTIONAL MATCH path2 = (p)-[:CONTAINS_ILLUSTRATION]->(i:Illustration)
OPTIONAL MATCH path3 = (p)-[:CITES]->(l:Literature)
RETURN path1, path2, path3
```

### 13. Последовательность параграфов с контентом
```cypher
MATCH (s:Section {id: "chapter_глава-i-система-новейших-фундаментальных-открытий_section-1-вселенная-как-объект-научного-исследования"})-[:HAS_PARAGRAPH]->(first:Paragraph)
WHERE NOT exists((first)<-[:NEXT]-())
MATCH path = (first)-[:NEXT*0..10]->(p:Paragraph)
OPTIONAL MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
OPTIONAL MATCH (p)-[:CITES]->(l:Literature)
RETURN p.order,
       p.content,
       collect(DISTINCT f.latex) as formulas,
       collect(DISTINCT l.number) as citations
ORDER BY p.order
```

## Поиск и анализ

### 14. Поиск параграфов по содержанию (fulltext search требует настройки)
```cypher
MATCH (p:Paragraph)
WHERE p.content CONTAINS "гравитация"
RETURN p.id, 
       p.order,
       left(p.content, 150) as preview
LIMIT 10
```

### 15. Самые длинные параграфы
```cypher
MATCH (p:Paragraph)
RETURN p.id, 
       p.word_count,
       left(p.content, 100) as preview
ORDER BY p.word_count DESC
LIMIT 20
```

### 16. Параграфы с наибольшим количеством формул
```cypher
MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
WITH p, count(f) as formula_count
WHERE formula_count > 5
RETURN p.id,
       formula_count,
       left(p.content, 100) as preview
ORDER BY formula_count DESC
LIMIT 20
```

### 17. Найти все использования конкретного символа
```cypher
MATCH (sym:Symbol {latex: "\\alpha"})<-[:USES_SYMBOL]-(f:Formula)<-[:CONTAINS_FORMULA]-(p:Paragraph)
RETURN DISTINCT p.id,
       left(p.content, 100) as preview,
       collect(f.latex)[0..3] as sample_formulas
LIMIT 20
```

## Экспорт данных

### 18. Экспорт структуры главы для анализа
```cypher
MATCH (ch:Chapter)-[:HAS_SECTION]->(s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
WHERE ch.id = "chapter_глава-i-система-новейших-фундаментальных-открытий"
RETURN ch.title as chapter,
       s.order as section_order,
       s.number as section_number,
       s.title as section_title,
       p.order as paragraph_order,
       p.word_count as word_count,
       p.content as content
ORDER BY s.order, p.order
```

### 19. Матрица связности: какие секции цитируют какие источники
```cypher
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CITES]->(l:Literature)
WITH s, l, count(*) as citation_count
RETURN s.number as section,
       s.title as section_title,
       collect({number: l.number, author: l.author, count: citation_count}) as citations
ORDER BY s.order
```

## Обслуживание

### 20. Проверка целостности связей NEXT
```cypher
// Найти параграфы без следующего (последние в секции - это нормально)
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
WHERE NOT exists((p)-[:NEXT]->())
WITH s, count(p) as orphan_count
WHERE orphan_count > 1
RETURN s.id, s.title, orphan_count
```

### 21. Найти разрывы в последовательности
```cypher
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p1:Paragraph)
MATCH (s)-[:HAS_PARAGRAPH]->(p2:Paragraph)
WHERE p1.order + 1 = p2.order
  AND NOT exists((p1)-[:NEXT]->(p2))
RETURN s.id, p1.order, p2.order
```

### 22. Общая статистика графа
```cypher
MATCH (b:Book)
OPTIONAL MATCH (b)-[:HAS_CHAPTER]->(ch:Chapter)
OPTIONAL MATCH (ch)-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
OPTIONAL MATCH ()-[next:NEXT]->()
OPTIONAL MATCH ()-[contains:CONTAINS_FORMULA|CONTAINS_ILLUSTRATION|CONTAINS_TABLE]->()
OPTIONAL MATCH ()-[cites:CITES]->()
RETURN count(DISTINCT b) as books,
       count(DISTINCT ch) as chapters,
       count(DISTINCT s) as sections,
       count(DISTINCT p) as paragraphs,
       count(DISTINCT next) as next_links,
       count(DISTINCT contains) as content_links,
       count(DISTINCT cites) as citations
```
