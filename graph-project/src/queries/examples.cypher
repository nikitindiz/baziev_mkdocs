-- Примеры Cypher запросов для графа знаний "Физика Базиева"

-- 1. Найти все формулы в разделе
MATCH (s:Section {id: 'section_1'})-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
RETURN f.latex, f.metadata.equation_number
ORDER BY f.metadata.equation_number;

-- 2. Трассировка вывода формулы
MATCH path = (f1:Formula {metadata: {equation_number: '(1.25)'}})-[:DERIVED_FROM*]->(f2:Formula)
RETURN path;

-- 3. Найти все использования символа
MATCH (s:Symbol {latex: '\\varepsilon_i'})<-[:USES_SYMBOL]-(f:Formula)<-[:CONTAINS_FORMULA]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(sec:Section)
RETURN sec.title, f.metadata.equation_number, f.latex;

-- 4. Поиск связанных концепций
MATCH (c1:Concept {name: 'Глобула'})-[r:RELATED_TO]-(c2:Concept)
RETURN c2.name, r.relation_type, r.strength
ORDER BY r.strength DESC;

-- 5. Самые цитируемые источники
MATCH (l:Literature)<-[:CITES]-(p:Paragraph)
WITH l, count(p) as citation_count
RETURN l.author, l.title, citation_count
ORDER BY citation_count DESC
LIMIT 10;

-- 6. Найти разделы, использующие определенную концепцию
MATCH (c:Concept {name: 'Осциллятор'})<-[:MENTIONS]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(s:Section)
RETURN DISTINCT s.title, s.file_path;

-- 7. Иллюстрации с формулами в подписи
MATCH (i:Illustration)-[:FORMULA_IN_CAPTION]->(f:Formula)
RETURN i.caption, collect(f.latex) as formulas;

-- 8. Найти формулы, используемые в таблицах
MATCH (t:Table)-[:TABLE_CONTAINS_FORMULA]->(f:Formula)
RETURN t.id, f.latex;

-- 9. Путь между двумя концепциями
MATCH path = shortestPath(
  (c1:Concept {name: 'Глобула'})-[*..5]-(c2:Concept {name: 'Сверхпроводимость'})
)
RETURN path;

-- 10. Найти все формулы, не имеющие символов
MATCH (f:Formula)
WHERE NOT (f)-[:USES_SYMBOL]->()
RETURN f.latex, f.type;

-- 11. Статистика по главам
MATCH (ch:Chapter)
OPTIONAL MATCH (ch)-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
OPTIONAL MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
WITH ch, count(DISTINCT s) as sections,
     count(DISTINCT p) as paragraphs,
     count(DISTINCT f) as formulas
RETURN ch.title, sections, paragraphs, formulas
ORDER BY ch.order;

-- 12. Найти наиболее "важные" формулы (по количеству связей)
MATCH (f:Formula)
WITH f, size((f)--()) as connections
RETURN f.latex, f.metadata.equation_number, connections
ORDER BY connections DESC
LIMIT 20;

-- 13. Полнотекстовый поиск по параграфам
CALL db.index.fulltext.queryNodes('paragraph_content', 'кинетическая энергия')
YIELD node, score
MATCH (node)<-[:HAS_PARAGRAPH]-(s:Section)
RETURN node.content, s.title, score
ORDER BY score DESC
LIMIT 10;

-- 14. Найти все формулы, связанные с конкретной формулой
MATCH (f:Formula {id: 'formula_hash'})-[r]-(related)
RETURN type(r) as relationship_type, labels(related) as related_type, related
LIMIT 50;

-- 15. Граф цитирования (какие разделы цитируют какие источники)
MATCH (s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CITES]->(l:Literature)
RETURN s.title, collect(DISTINCT l.number) as cited_literature
ORDER BY s.order;
