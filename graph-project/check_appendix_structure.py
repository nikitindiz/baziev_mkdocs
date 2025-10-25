#!/usr/bin/env python3
"""Проверка структуры глав-приложений"""

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

# Проверить структуру глав-приложений
with driver.session() as session:
    # 1. Найти главы-приложения
    query1 = """
    MATCH (c:Chapter)
    WHERE c.id STARTS WITH 'chapter_приложение'
    RETURN c.id as chapter_id, c.title as chapter_title
    ORDER BY c.id
    """
    
    print("=== Главы-приложения ===\n")
    result = session.run(query1)
    chapters = list(result)
    
    for record in chapters:
        print(f"{record['chapter_id']}")
        print(f"  title: {record['chapter_title']}\n")
    
    # 2. Проверить наличие секций
    query2 = """
    MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
    WHERE c.id STARTS WITH 'chapter_приложение'
    RETURN count(s) as section_count
    """
    
    result = session.run(query2)
    count = result.single()['section_count']
    print(f"Секций в приложениях: {count}\n")
    
    # 3. Проверить наличие параграфов
    query3 = """
    MATCH (c:Chapter)-[:HAS_SECTION|HAS_PARAGRAPH*]->(p:Paragraph)
    WHERE c.id STARTS WITH 'chapter_приложение'
    RETURN c.id as chapter_id, count(p) as paragraph_count
    ORDER BY c.id
    """
    
    print("=== Параграфы в приложениях ===\n")
    result = session.run(query3)
    for record in result:
        print(f"{record['chapter_id']}: {record['paragraph_count']} параграфов")
    
    # 4. Проверить orphan таблицы в приложениях
    query4 = """
    MATCH (t:Table)
    WHERE NOT (t)<-[:CONTAINS_TABLE]-()
      AND t.source CONTAINS 'приложение'
    RETURN t.id as table_id, t.source as source
    """
    
    print("\n=== Orphan таблицы в приложениях ===\n")
    result = session.run(query4)
    orphans = list(result)
    
    for record in orphans:
        print(f"Table: {record['table_id']}")
        print(f"  Source: {record['source']}\n")
    
    print(f"Всего orphan таблиц в приложениях: {len(orphans)}")

driver.close()
