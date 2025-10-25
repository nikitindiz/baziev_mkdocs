#!/usr/bin/env python3
"""
Проверка порядка параграфов в первой секции первой главы
"""
import yaml
from src.utils.neo4j_connection import Neo4jConnection


def check_paragraph_order():
    """Проверить порядок параграфов"""
    
    # Загрузить конфигурацию
    with open('config/config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Подключиться к Neo4j
    neo4j = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    print("=" * 100)
    print("ПАРАГРАФЫ ИЗ NEO4J (первая секция первой главы)")
    print("=" * 100)
    
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
    RETURN ch.title as chapter,
           s.number as section_num,
           s.title as section_title,
           s.file_path as file_path,
           p.order as para_order,
           p.content as content
    ORDER BY p.order
    LIMIT 3
    """
    
    results = neo4j.execute_query(query)
    
    if results:
        print(f"\nГлава: {results[0]['chapter']}")
        print(f"Секция: {results[0]['section_num']} - {results[0]['section_title']}")
        print(f"Файл: {results[0]['file_path']}\n")
        
        for i, r in enumerate(results, 1):
            print(f"\n{'='*100}")
            print(f"Параграф #{r['para_order']} (порядковый номер: {i})")
            print(f"{'='*100}")
            print(r['content'])
    else:
        print("Параграфы не найдены!")
    
    neo4j.close()


if __name__ == '__main__':
    check_paragraph_order()
