#!/usr/bin/env python3
"""Проверка последней orphan таблицы"""

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
    # Проверить таблицу ba4c04131989
    query = """
    MATCH (t:Table {id: 'ba4c04131989'})
    RETURN t.id as id, t.source as source, t.caption as caption, t.content as content
    """
    
    result = session.run(query).single()
    
    if result:
        table_id = result['id']
        source = json.loads(result['source']) if result['source'] else {}
        caption = result['caption']
        content = result['content'][:200] if result['content'] else 'No content'
        
        print(f"=== Таблица {table_id} ===\n")
        print(f"Source: {source}")
        print(f"Caption: {caption}")
        print(f"Content: {content}...\n")
        
        file_path = source.get('file', '')
        
        if file_path:
            parts = file_path.split('/')
            chapter_id = parts[0]
            
            print(f"Computed chapter_id: {chapter_id}\n")
            
            # Проверить главу
            chapter_query = """
            MATCH (c:Chapter {id: $chapter_id})
            RETURN c.id as id, c.title as title
            """
            
            chapter_result = session.run(chapter_query, chapter_id=chapter_id).single()
            
            if chapter_result:
                print(f"✓ Глава найдена: {chapter_result['id']}")
                print(f"  Title: {chapter_result['title']}\n")
                
                # Проверить секции
                sections_query = """
                MATCH (c:Chapter {id: $chapter_id})-[:HAS_SECTION]->(s:Section)
                RETURN count(s) as section_count
                """
                
                sections_result = session.run(sections_query, chapter_id=chapter_id).single()
                section_count = sections_result['section_count']
                
                print(f"Секций в главе: {section_count}\n")
                
                if section_count > 0:
                    # Попробовать найти связь с секцией
                    file_name = parts[1].replace('.md', '') if len(parts) > 1 else 'index'
                    section_id = f"{chapter_id}_{file_name}"
                    
                    print(f"Computed section_id: {section_id}\n")
                    
                    section_query = """
                    MATCH (s:Section {id: $section_id})
                    RETURN s.id as id, s.title as title
                    """
                    
                    section_result = session.run(section_query, section_id=section_id).single()
                    
                    if section_result:
                        print(f"✓ Секция найдена: {section_result['id']}")
                        print(f"  Title: {section_result['title']}")
                    else:
                        print(f"❌ Секция НЕ найдена: {section_id}")
                        print("\nПоказать все секции в главе:")
                        
                        all_sections_query = """
                        MATCH (c:Chapter {id: $chapter_id})-[:HAS_SECTION]->(s:Section)
                        RETURN s.id as id, s.title as title
                        ORDER BY s.id
                        """
                        
                        all_sections = list(session.run(all_sections_query, chapter_id=chapter_id))
                        for s in all_sections:
                            print(f"  - {s['id']}")
            else:
                print(f"❌ Глава НЕ найдена: {chapter_id}")

driver.close()
