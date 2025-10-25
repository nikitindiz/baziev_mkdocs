#!/usr/bin/env python3
"""
Проверка связей таблиц с параграфами
"""
import yaml
from src.utils.neo4j_connection import Neo4jConnection


def check_table_links():
    """Проверить связи таблиц"""
    
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
    print("ПРОВЕРКА СВЯЗЕЙ ТАБЛИЦ")
    print("=" * 100)
    
    # 1. Получить информацию о конкретной таблице
    query = """
    MATCH (t:Table)
    WHERE elementId(t) = $element_id
    RETURN t.id as id,
           t.title as title,
           t.caption as caption,
           elementId(t) as element_id
    """
    
    element_id = "4:ada0754e-bb1f-4a0f-9369-70ac494ff593:9602"
    result = neo4j.execute_query(query, {"element_id": element_id})
    
    if result:
        print(f"\n✅ Найдена таблица:")
        print(f"   ID: {result[0]['id']}")
        print(f"   Title: {result[0]['title']}")
        print(f"   Caption: {result[0].get('caption', 'N/A')}")
        print(f"   Element ID: {result[0]['element_id']}")
        table_id = result[0]['id']
    else:
        print(f"\n❌ Таблица с element_id={element_id} не найдена")
        return
    
    # 2. Проверить есть ли связи CONTAINS_TABLE
    print(f"\n{'='*100}")
    print("ПОИСК СВЯЗЕЙ CONTAINS_TABLE")
    print(f"{'='*100}")
    
    query = """
    MATCH (p:Paragraph)-[r:CONTAINS_TABLE]->(t:Table {id: $table_id})
    RETURN p.id as para_id,
           left(p.content, 100) as content,
           r.position as position
    """
    
    results = neo4j.execute_query(query, {"table_id": table_id})
    
    if results:
        print(f"\n✅ Найдено связей: {len(results)}")
        for r in results:
            print(f"\n   Параграф: {r['para_id']}")
            print(f"   Позиция: {r['position']}")
            print(f"   Содержание: {r['content']}...")
    else:
        print(f"\n❌ Связей CONTAINS_TABLE не найдено!")
    
    # 3. Проверить все таблицы и их связи (от любых узлов)
    print(f"\n{'='*100}")
    print("СТАТИСТИКА ПО ВСЕМ ТАБЛИЦАМ")
    print(f"{'='*100}")
    
    query = """
    MATCH (t:Table)
    OPTIONAL MATCH (n)-[:CONTAINS_TABLE]->(t)
    WITH t, count(n) as link_count, collect(labels(n)[0]) as link_types
    RETURN t.id as id,
           t.title as title,
           link_count,
           link_types
    ORDER BY link_count DESC, t.id
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nВсего таблиц: {len(results)}")
    
    linked = sum(1 for r in results if r['link_count'] > 0)
    unlinked = sum(1 for r in results if r['link_count'] == 0)
    
    print(f"Со связями: {linked}")
    print(f"Без связей: {unlinked}")
    
    print(f"\nТаблицы БЕЗ связей:")
    for r in results:
        if r['link_count'] == 0:
            print(f"  - {r['id']}: {r['title']}")
    
    print(f"\nРаспределение по типам связей:")
    from collections import Counter
    all_types = []
    for r in results:
        all_types.extend(r['link_types'])
    type_counts = Counter(all_types)
    for link_type, count in type_counts.items():
        print(f"  {link_type}: {count}")
    
    # 4. Проверить содержат ли параграфы ссылки на таблицы
    print(f"\n{'='*100}")
    print("ПОИСК ССЫЛОК НА ТАБЛИЦЫ В ПАРАГРАФАХ")
    print(f"{'='*100}")
    
    query = """
    MATCH (p:Paragraph)
    WHERE p.content CONTAINS '{{table:'
    RETURN p.id as para_id,
           p.content as content
    LIMIT 5
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nНайдено параграфов со ссылками на таблицы: {len(results)}")
    
    if results:
        import re
        table_pattern = re.compile(r'\{\{table:([a-f0-9]{12})\}\}')
        
        for r in results:
            matches = table_pattern.findall(r['content'])
            print(f"\n  Параграф: {r['para_id']}")
            print(f"  Ссылки на таблицы: {matches}")
            print(f"  Содержание: {r['content'][:150]}...")
    
    # 5. Проверить одну конкретную таблицу с её ID
    print(f"\n{'='*100}")
    print("ПРОВЕРКА КОНКРЕТНОЙ ТАБЛИЦЫ")
    print(f"{'='*100}")
    
    query = """
    MATCH (t:Table {id: $table_id})
    RETURN t.id as id,
           t.title as title,
           keys(t) as properties
    """
    
    result = neo4j.execute_query(query, {"table_id": table_id})
    
    if result:
        print(f"\nСвойства таблицы {table_id}:")
        for key, value in result[0].items():
            print(f"  {key}: {value}")
    
    # 6. Проверить процесс связывания в коде
    print(f"\n{'='*100}")
    print("ПРОВЕРКА: ЕСТЬ ЛИ ВООБЩЕ СВЯЗИ CONTAINS_TABLE?")
    print(f"{'='*100}")
    
    query = """
    MATCH ()-[r:CONTAINS_TABLE]->()
    RETURN count(r) as total_table_links
    """
    
    result = neo4j.execute_query(query)
    
    if result:
        total = result[0]['total_table_links']
        print(f"\nВсего связей CONTAINS_TABLE в графе: {total}")
        
        if total == 0:
            print("\n⚠️  ПРОБЛЕМА: Связи CONTAINS_TABLE вообще не создаются!")
            print("   Возможные причины:")
            print("   1. В параграфах нет ссылок вида {{table:id}}")
            print("   2. Метод _create_contains_table_link не вызывается")
            print("   3. ID таблиц в параграфах не совпадают с ID в базе")
    
    neo4j.close()
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    check_table_links()
