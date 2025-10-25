#!/usr/bin/env python3
"""
Тестовый скрипт для проверки навигации по параграфам через связи NEXT
"""
import yaml
from src.utils.neo4j_connection import Neo4jConnection


def test_paragraph_navigation():
    """Тестирование навигации по параграфам"""
    
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
    
    print("=" * 80)
    print("Тест 1: Получить первую секцию и её параграфы в порядке следования")
    print("=" * 80)
    
    query = """
    MATCH (ch:Chapter)-[:HAS_SECTION]->(s:Section)
    WITH s
    ORDER BY s.order
    LIMIT 1
    MATCH (s)-[:HAS_PARAGRAPH]->(first:Paragraph)
    WHERE NOT exists((first)<-[:NEXT]-())
    MATCH path = (first)-[:NEXT*0..5]->(p:Paragraph)
    RETURN s.title as section,
           p.order as order,
           left(p.content, 100) as preview,
           length(path) as depth
    ORDER BY depth
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nСекция: {results[0]['section'] if results else 'N/A'}")
    print(f"Найдено параграфов: {len(results)}")
    print("\nПараграфы:")
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Параграф #{r['order']}")
        print(f"   {r['preview']}...")
    
    print("\n" + "=" * 80)
    print("Тест 2: Проверка связей NEXT между секциями")
    print("=" * 80)
    
    query = """
    MATCH (ch:Chapter)
    WITH ch
    ORDER BY ch.order
    LIMIT 1
    MATCH (ch)-[:HAS_SECTION]->(first:Section)
    WHERE NOT exists((first)<-[:NEXT]-())
    MATCH path = (first)-[:NEXT*0..3]->(s:Section)
    RETURN ch.title as chapter,
           s.number as number,
           s.title as title,
           length(path) as position
    ORDER BY position
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nГлава: {results[0]['chapter'] if results else 'N/A'}")
    print(f"Найдено секций: {len(results)}")
    print("\nСекции в порядке следования:")
    
    for i, r in enumerate(results, 1):
        print(f"{i}. {r['number']} - {r['title']}")
    
    print("\n" + "=" * 80)
    print("Тест 3: Статистика связей NEXT")
    print("=" * 80)
    
    query = """
    MATCH ()-[r:NEXT]->()
    WITH type(r) as rel_type, count(r) as count
    RETURN rel_type, count
    """
    
    results = neo4j.execute_query(query)
    
    for r in results:
        print(f"Связей {r['rel_type']}: {r['count']}")
    
    # Подробная статистика
    query = """
    MATCH (p:Paragraph)-[:NEXT]->()
    WITH count(p) as para_next
    MATCH (s:Section)-[:NEXT]->()
    WITH para_next, count(s) as section_next
    MATCH (p2:Paragraph)
    WITH para_next, section_next, count(p2) as total_paras
    MATCH (s2:Section)
    RETURN para_next as paragraphs_with_next,
           total_paras as total_paragraphs,
           section_next as sections_with_next,
           count(s2) as total_sections,
           (para_next * 100.0 / total_paras) as para_coverage,
           (section_next * 100.0 / count(s2)) as section_coverage
    """
    
    results = neo4j.execute_query(query)
    
    if results:
        r = results[0]
        print(f"\nПараграфы с NEXT: {r['paragraphs_with_next']} / {r['total_paragraphs']} ({r['para_coverage']:.1f}%)")
        print(f"Секции с NEXT: {r['sections_with_next']} / {r['total_sections']} ({r['section_coverage']:.1f}%)")
    
    print("\n" + "=" * 80)
    print("Тест 4: Найти параграфы без NEXT (последние в секциях)")
    print("=" * 80)
    
    query = """
    MATCH (s:Section)-[:HAS_PARAGRAPH]->(p:Paragraph)
    WHERE NOT exists((p)-[:NEXT]->())
    WITH s, count(p) as last_paras
    RETURN s.number as section,
           s.title as title,
           last_paras
    ORDER BY s.order
    LIMIT 5
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nНайдено секций: {len(results)}")
    for r in results:
        print(f"{r['section']}: {r['title']} - {r['last_paras']} конечных параграфов")
    
    neo4j.close()
    print("\n✅ Все тесты выполнены успешно!")


if __name__ == '__main__':
    test_paragraph_navigation()
