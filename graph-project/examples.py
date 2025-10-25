"""
Примеры использования Graph API
"""
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection
from src.queries.graph_queries import GraphQueries


def example_1_formula_search():
    """Пример 1: Поиск формул в разделе"""
    print("\n=== Пример 1: Поиск формул в разделе ===\n")
    
    config = load_config()
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    queries = GraphQueries(conn)
    
    # Получить первый раздел
    sections = conn.execute_query("MATCH (s:Section) RETURN s.id as id LIMIT 1")
    
    if sections:
        section_id = sections[0]['id']
        results = queries.formulas_in_section(section_id)
        
        print(f"Формулы в разделе {section_id}:")
        for r in results:
            print(f"  [{r.get('equation_number', 'N/A')}] {r['latex'][:60]}...")
    
    conn.close()


def example_2_symbol_usage():
    """Пример 2: Анализ использования символов"""
    print("\n=== Пример 2: Использование символов ===\n")
    
    config = load_config()
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    # Получить топ-10 наиболее используемых символов
    query = """
    MATCH (s:Symbol)<-[:USES_SYMBOL]-(f:Formula)
    WITH s, count(f) as usage_count
    RETURN s.latex as symbol, s.description as description, usage_count
    ORDER BY usage_count DESC
    LIMIT 10
    """
    
    results = conn.execute_query(query)
    
    print("Топ-10 наиболее используемых символов:")
    for r in results:
        print(f"  {r['symbol']:30} | {r['description'][:40]:40} | {r['usage_count']} использований")
    
    conn.close()


def example_3_citation_analysis():
    """Пример 3: Анализ цитирования"""
    print("\n=== Пример 3: Анализ цитирования литературы ===\n")
    
    config = load_config()
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    queries = GraphQueries(conn)
    results = queries.top_cited_literature(10)
    
    print("Топ-10 цитируемых источников:")
    for r in results:
        print(f"  [{r['number']}] {r['author']}: {r['title'][:50]}")
        print(f"      Цитирований: {r['citation_count']}")
    
    conn.close()


def example_4_chapter_statistics():
    """Пример 4: Статистика по главам"""
    print("\n=== Пример 4: Статистика по главам ===\n")
    
    config = load_config()
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    queries = GraphQueries(conn)
    results = queries.chapter_statistics()
    
    print(f"{'Глава':<60} | Разделы | Параграфы | Формулы")
    print("-" * 100)
    for r in results:
        print(f"{r['chapter'][:60]:<60} | {r['sections']:^7} | {r['paragraphs']:^10} | {r['formulas']:^7}")
    
    conn.close()


def example_5_custom_query():
    """Пример 5: Кастомный запрос - связь между разделами через формулы"""
    print("\n=== Пример 5: Связи между разделами через общие формулы ===\n")
    
    config = load_config()
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    # Найти разделы, которые используют одинаковые формулы
    query = """
    MATCH (s1:Section)-[:HAS_PARAGRAPH]->(:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)<-[:CONTAINS_FORMULA]-(:Paragraph)<-[:HAS_PARAGRAPH]-(s2:Section)
    WHERE s1.order < s2.order AND s1 <> s2
    WITH s1, s2, count(DISTINCT f) as shared_formulas
    WHERE shared_formulas > 2
    RETURN s1.title as section1, s2.title as section2, shared_formulas
    ORDER BY shared_formulas DESC
    LIMIT 10
    """
    
    results = conn.execute_query(query)
    
    print("Разделы с общими формулами:")
    for r in results:
        print(f"  {r['section1'][:40]:40} <-> {r['section2'][:40]:40}")
        print(f"    Общих формул: {r['shared_formulas']}")
    
    conn.close()


if __name__ == '__main__':
    print("\n" + "=" * 100)
    print("ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ГРАФА ЗНАНИЙ - ФИЗИКА БАЗИЕВА")
    print("=" * 100)
    
    try:
        example_1_formula_search()
        example_2_symbol_usage()
        example_3_citation_analysis()
        example_4_chapter_statistics()
        example_5_custom_query()
        
        print("\n" + "=" * 100)
        print("Все примеры успешно выполнены!")
        print("=" * 100 + "\n")
        
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        print("Убедитесь, что:")
        print("  1. Neo4j запущен")
        print("  2. Данные импортированы (python main.py import all)")
        print("  3. Настройки в config/config.yml корректны")
