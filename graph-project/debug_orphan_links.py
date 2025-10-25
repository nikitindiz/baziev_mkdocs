#!/usr/bin/env python3
"""
Отладка связывания orphan таблиц
"""
import yaml
import json
from src.utils.neo4j_connection import Neo4jConnection

with open('config/config.yml') as f:
    config = yaml.safe_load(f)

neo4j = Neo4jConnection(
    uri=config['neo4j']['uri'],
    user=config['neo4j']['username'],
    password=config['neo4j']['password'],
    database=config['neo4j']['database']
)

# Найти таблицы без связей
query = """
MATCH (t:Table)
WHERE NOT exists((:Paragraph)-[:CONTAINS_TABLE]->(t))
  AND NOT exists((:Section)-[:CONTAINS_TABLE]->(t))
RETURN t.id as id, t.source as source
LIMIT 5
"""

orphan_tables = neo4j.execute_query(query)

print(f"Найдено orphan таблиц: {len(orphan_tables)}\n")

for table in orphan_tables:
    table_id = table['id']
    source = table.get('source')
    
    print(f"Таблица: {table_id}")
    
    if not source:
        print("  ❌ Нет source\n")
        continue
    
    try:
        source_data = json.loads(source) if isinstance(source, str) else source
        file_path = source_data.get('file', '')
        
        print(f"  Source file: {file_path}")
        
        if '/' in file_path:
            parts = file_path.split('/')
            chapter_part = parts[0]
            file_name = parts[1].replace('.md', '')
            
            section_id = f"{chapter_part}_{file_name}"
            
            print(f"  Вычисленный section_id: {section_id}")
            
            # Проверить существует ли секция
            check_query = """
            MATCH (s:Section {id: $section_id})
            RETURN s.id, s.title
            """
            
            section_result = neo4j.execute_query(check_query, {"section_id": section_id})
            
            if section_result:
                print(f"  ✅ Секция найдена: {section_result[0]['title']}")
                
                # Попробуем создать связь
                link_query = """
                MATCH (s:Section {id: $section_id})
                MATCH (t:Table {id: $table_id})
                MERGE (s)-[r:CONTAINS_TABLE]->(t)
                SET r.orphan = true
                RETURN r
                """
                
                result = neo4j.execute_query(link_query, {
                    "section_id": section_id,
                    "table_id": table_id
                })
                
                if result:
                    print(f"  ✅ Связь создана!")
                else:
                    print(f"  ⚠️  Связь не создана (возможно уже существует)")
            else:
                print(f"  ❌ Секция не найдена!")
                
                # Поискать похожие
                search_query = """
                MATCH (s:Section)
                WHERE s.id CONTAINS $keyword
                RETURN s.id
                LIMIT 3
                """
                
                keyword = chapter_part[:30]
                similar = neo4j.execute_query(search_query, {"keyword": keyword})
                if similar:
                    print(f"  Похожие секции:")
                    for s in similar:
                        print(f"    - {s['id']}")
        else:
            print(f"  ⚠️  Некорректный путь файла")
        
    except (json.JSONDecodeError, KeyError, AttributeError) as e:
        print(f"  ❌ Ошибка парсинга: {e}")
    
    print()

neo4j.close()
