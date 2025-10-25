#!/usr/bin/env python3
"""Полная статистика импортированного графа знаний"""

from neo4j import GraphDatabase
import yaml

# Загрузка конфигурации
with open('config/config.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

neo4j_config = config['neo4j']
driver = GraphDatabase.driver(
    neo4j_config['uri'],
    auth=(neo4j_config['username'], neo4j_config['password']),
    database=neo4j_config['database']
)

print("=" * 80)
print("СТАТИСТИКА ГРАФА ЗНАНИЙ - Физика Базиева")
print("=" * 80)

with driver.session() as session:
    # 1. Узлы
    print("\n📊 УЗЛЫ:\n")
    
    node_types = ['Book', 'Chapter', 'Section', 'Paragraph', 'Formula', 'Symbol', 
                  'Illustration', 'Table', 'Literature']
    
    for node_type in node_types:
        query = f"MATCH (n:{node_type}) RETURN count(n) as count"
        result = session.run(query).single()
        count = result['count']
        print(f"  {node_type:15} {count:>6}")
    
    # Общее количество
    query = "MATCH (n) RETURN count(n) as total"
    total = session.run(query).single()['total']
    print(f"  {'-' * 23}")
    print(f"  {'ВСЕГО':15} {total:>6}")
    
    # 2. Связи
    print("\n🔗 СВЯЗИ:\n")
    
    rel_types = [
        'HAS_CHAPTER', 'HAS_SECTION', 'HAS_PARAGRAPH', 'NEXT',
        'CONTAINS_FORMULA', 'CONTAINS_TABLE', 'CONTAINS_ILLUSTRATION', 'CITES'
    ]
    
    for rel_type in rel_types:
        query = f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count"
        result = session.run(query).single()
        count = result['count']
        print(f"  {rel_type:25} {count:>6}")
    
    # Общее количество
    query = "MATCH ()-[r]->() RETURN count(r) as total"
    total_rels = session.run(query).single()['total']
    print(f"  {'-' * 33}")
    print(f"  {'ВСЕГО':25} {total_rels:>6}")
    
    # 3. Детализация по артефактам
    print("\n📚 ДЕТАЛИЗАЦИЯ АРТЕФАКТОВ:\n")
    
    # Формулы
    query = """
    MATCH (f:Formula)
    OPTIONAL MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
    WITH f, count(p) as para_count
    RETURN 
        count(f) as total,
        sum(CASE WHEN para_count > 0 THEN 1 ELSE 0 END) as linked,
        sum(CASE WHEN para_count = 0 THEN 1 ELSE 0 END) as orphan
    """
    result = session.run(query).single()
    print(f"  Формулы:")
    print(f"    Всего:   {result['total']:>6}")
    print(f"    Со связями: {result['linked']:>6}")
    print(f"    Без связей: {result['orphan']:>6}")
    
    # Таблицы
    query = """
    MATCH (t:Table)
    OPTIONAL MATCH (n)-[:CONTAINS_TABLE]->(t)
    WITH t, count(n) as link_count, collect(labels(n)[0]) as link_types
    RETURN 
        count(t) as total,
        sum(CASE WHEN link_count > 0 THEN 1 ELSE 0 END) as linked,
        sum(CASE WHEN link_count = 0 THEN 1 ELSE 0 END) as orphan,
        sum(CASE WHEN 'Paragraph' IN link_types THEN 1 ELSE 0 END) as from_paragraph,
        sum(CASE WHEN 'Chapter' IN link_types THEN 1 ELSE 0 END) as from_chapter
    """
    result = session.run(query).single()
    print(f"\n  Таблицы:")
    print(f"    Всего:   {result['total']:>6}")
    print(f"    Со связями: {result['linked']:>6}")
    print(f"      - от Paragraph: {result['from_paragraph']:>6}")
    print(f"      - от Chapter:   {result['from_chapter']:>6}")
    print(f"    Без связей: {result['orphan']:>6}")
    
    # Иллюстрации
    query = """
    MATCH (i:Illustration)
    OPTIONAL MATCH (n)-[:CONTAINS_ILLUSTRATION]->(i)
    WITH i, count(n) as link_count, collect(labels(n)[0]) as link_types
    RETURN 
        count(i) as total,
        sum(CASE WHEN link_count > 0 THEN 1 ELSE 0 END) as linked,
        sum(CASE WHEN link_count = 0 THEN 1 ELSE 0 END) as orphan,
        sum(CASE WHEN 'Paragraph' IN link_types THEN 1 ELSE 0 END) as from_paragraph,
        sum(CASE WHEN 'Chapter' IN link_types THEN 1 ELSE 0 END) as from_chapter
    """
    result = session.run(query).single()
    print(f"\n  Иллюстрации:")
    print(f"    Всего:   {result['total']:>6}")
    print(f"    Со связями: {result['linked']:>6}")
    print(f"      - от Paragraph: {result['from_paragraph']:>6}")
    print(f"      - от Chapter:   {result['from_chapter']:>6}")
    print(f"    Без связей: {result['orphan']:>6}")
    
    # Литература
    query = """
    MATCH (l:Literature)
    OPTIONAL MATCH (p:Paragraph)-[:CITES]->(l)
    WITH l, count(p) as para_count
    RETURN 
        count(l) as total,
        sum(CASE WHEN para_count > 0 THEN 1 ELSE 0 END) as linked,
        sum(CASE WHEN para_count = 0 THEN 1 ELSE 0 END) as orphan
    """
    result = session.run(query).single()
    print(f"\n  Литература:")
    print(f"    Всего:   {result['total']:>6}")
    print(f"    Со связями: {result['linked']:>6}")
    print(f"    Без связей: {result['orphan']:>6}")
    
    # 4. Навигация
    print("\n🧭 НАВИГАЦИЯ (NEXT):\n")
    
    # NEXT между параграфами
    query = """
    MATCH (p1:Paragraph)-[:NEXT]->(p2:Paragraph)
    RETURN count(*) as count
    """
    para_next = session.run(query).single()['count']
    print(f"  Paragraph → Paragraph: {para_next:>6}")
    
    # NEXT между секциями
    query = """
    MATCH (s1:Section)-[:NEXT]->(s2:Section)
    RETURN count(*) as count
    """
    section_next = session.run(query).single()['count']
    print(f"  Section → Section:     {section_next:>6}")
    
    print(f"  {'-' * 30}")
    print(f"  {'ВСЕГО NEXT:':22} {para_next + section_next:>6}")
    
    # 5. Структура
    print("\n📖 СТРУКТУРА КНИГИ:\n")
    
    query = """
    MATCH (c:Chapter)
    OPTIONAL MATCH (c)-[:HAS_SECTION]->(s:Section)
    OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
    RETURN c.id as chapter_id, 
           count(DISTINCT s) as sections,
           count(DISTINCT p) as paragraphs
    ORDER BY c.id
    """
    
    results = list(session.run(query))
    total_sections = sum(r['sections'] for r in results)
    total_paragraphs = sum(r['paragraphs'] for r in results)
    
    print(f"  Глав:       {len(results):>6}")
    print(f"  Секций:     {total_sections:>6}")
    print(f"  Параграфов: {total_paragraphs:>6}")
    
    # Средние значения
    avg_sections = total_sections / len(results) if results else 0
    avg_paragraphs = total_paragraphs / len(results) if results else 0
    
    print(f"\n  Среднее на главу:")
    print(f"    Секций:     {avg_sections:>6.1f}")
    print(f"    Параграфов: {avg_paragraphs:>6.1f}")

driver.close()

print("\n" + "=" * 80)
print("✅ Импорт успешно завершен! Граф знаний готов к использованию.")
print("=" * 80 + "\n")
