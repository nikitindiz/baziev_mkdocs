#!/usr/bin/env python3
"""Проверка конкретно главы с orphan таблицами"""

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

with driver.session() as session:
    # Проверить связи Chapter->CONTAINS_TABLE для приложений
    query = """
    MATCH (c:Chapter)-[r:CONTAINS_TABLE]->(t:Table)
    WHERE c.id STARTS WITH 'chapter_приложение'
    RETURN c.id as chapter_id, c.title as chapter_title, 
           count(t) as table_count, collect(t.id) as table_ids
    ORDER BY c.id
    """
    
    print("=== Связи Chapter->CONTAINS_TABLE в приложениях ===\n")
    result = session.run(query)
    
    for record in result:
        print(f"Chapter: {record['chapter_id']}")
        print(f"  Title: {record['chapter_title']}")
        print(f"  Tables: {record['table_count']}")
        for table_id in record['table_ids']:
            print(f"    - {table_id}")
        print()
    
    # Проверить конкретную таблицу a596885158e9
    query2 = """
    MATCH (t:Table {id: 'a596885158e9'})
    OPTIONAL MATCH (n)-[r]->(t)
    RETURN t.id as table_id, t.source as source, 
           type(r) as rel_type, labels(n)[0] as from_type, n.id as from_id
    """
    
    print("=== Проверка таблицы a596885158e9 ===\n")
    result = session.run(query2)
    
    for record in result:
        print(f"Table: {record['table_id']}")
        print(f"  Source: {record['source']}")
        if record['rel_type']:
            print(f"  От: {record['from_type']} ({record['from_id']})")
            print(f"  Связь: {record['rel_type']}")
        else:
            print("  ❌ Связей НЕТ")

driver.close()
