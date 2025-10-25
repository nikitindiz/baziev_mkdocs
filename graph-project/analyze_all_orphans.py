#!/usr/bin/env python3
"""Полный анализ всех orphan таблиц"""

from neo4j import GraphDatabase
import yaml
import json

# Загрузка конфигурации
with open('config/config.yml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

neo4j_config = config['neo4j']
driver = GraphDatabase.driver(
    neo4j_config['uri'],
    auth=(neo4j_config['username'], neo4j_config['password']),
    database=neo4j_config['database']
)

with driver.session() as session:
    # Найти все orphan таблицы
    query = """
    MATCH (t:Table)
    WHERE NOT (t)<-[:CONTAINS_TABLE]-()
    RETURN t.id as table_id, t.source as source, t.caption as caption
    """
    
    result = session.run(query)
    orphans = list(result)
    
    print(f"=== Всего orphan таблиц: {len(orphans)} ===\n")
    
    for i, record in enumerate(orphans, 1):
        table_id = record['table_id']
        source = record['source']
        caption = record['caption'] or 'Нет заголовка'
        
        # Парсим source
        source_data = json.loads(source) if source else {}
        file_path = source_data.get('file', 'Нет файла')
        
        print(f"{i}. Table: {table_id}")
        print(f"   File: {file_path}")
        print(f"   Caption: {caption[:80]}..." if len(caption) > 80 else f"   Caption: {caption}")
        
        # Проверяем, есть ли chapter или section с таким путем
        parts = file_path.split('/')
        if len(parts) >= 2:
            chapter_part = parts[0]
            
            # Проверка главы
            chapter_query = """
            MATCH (c:Chapter)
            WHERE c.id = $chapter_id
            RETURN c.id as id, c.title as title
            """
            chapter_result = session.run(chapter_query, chapter_id=chapter_part).single()
            
            if chapter_result:
                print(f"   ✓ Глава найдена: {chapter_result['id']}")
                
                # Проверка секций в этой главе
                section_query = """
                MATCH (c:Chapter {id: $chapter_id})-[:HAS_SECTION]->(s:Section)
                RETURN s.id as section_id, s.title as section_title
                """
                sections = list(session.run(section_query, chapter_id=chapter_part))
                
                if sections:
                    print(f"   Секции в главе ({len(sections)}):")
                    for s in sections[:3]:  # Показать первые 3
                        print(f"     - {s['section_id']}")
                else:
                    print(f"   ⚠ Секций в главе НЕТ - нужно связывать с главой напрямую!")
            else:
                print(f"   ❌ Глава НЕ найдена: {chapter_part}")
        
        print()

driver.close()
