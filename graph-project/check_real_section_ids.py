#!/usr/bin/env python3
"""Проверка реальных ID секций для глав-приложений"""

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

# Найти все секции в главах приложений
query = """
MATCH (c:Chapter)-[:HAS_SECTION]->(s:Section)
WHERE c.id STARTS WITH 'chapter_приложение'
RETURN c.id as chapter_id, s.id as section_id, s.title as section_title
ORDER BY c.id, s.id
"""

with driver.session() as session:
    result = session.run(query)
    print("Главы-приложения и их секции:\n")
    
    current_chapter = None
    for record in result:
        chapter_id = record['chapter_id']
        section_id = record['section_id']
        section_title = record['section_title']
        
        if chapter_id != current_chapter:
            print(f"\n{chapter_id}:")
            current_chapter = chapter_id
        
        print(f"  - {section_id}")
        if section_title:
            print(f"    title: {section_title}")

driver.close()
