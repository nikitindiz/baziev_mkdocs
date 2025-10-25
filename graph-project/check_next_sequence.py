#!/usr/bin/env python3
"""
Проверка последовательности NEXT связей между параграфами
"""
import yaml
from src.utils.neo4j_connection import Neo4jConnection


def check_next_sequence():
    """Проверить корректность последовательности NEXT"""
    
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
    print("ПРОВЕРКА ПОСЛЕДОВАТЕЛЬНОСТИ NEXT В ПЕРВОЙ СЕКЦИИ")
    print("=" * 100)
    
    # 1. Найти первый параграф (без входящего NEXT)
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(first:Paragraph)
    WHERE NOT exists((first)<-[:NEXT]-())
    RETURN s.title as section,
           first.id as id,
           first.order as order,
           left(first.content, 100) as preview
    """
    
    result = neo4j.execute_query(query)
    
    if result:
        print(f"\n✅ Найден первый параграф (без входящего NEXT):")
        print(f"   ID: {result[0]['id']}")
        print(f"   Order: {result[0]['order']}")
        print(f"   Секция: {result[0]['section']}")
        print(f"   Содержание: {result[0]['preview']}...")
    else:
        print("\n❌ Первый параграф не найден!")
        return
    
    # 2. Пройти по цепочке NEXT и показать первые 5 параграфов
    print(f"\n{'='*100}")
    print("ЦЕПОЧКА NEXT (первые 5 параграфов)")
    print(f"{'='*100}")
    
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(first:Paragraph)
    WHERE NOT exists((first)<-[:NEXT]-())
    MATCH path = (first)-[:NEXT*0..4]->(p:Paragraph)
    RETURN p.id as id,
           p.order as order,
           length(path) as position,
           left(p.content, 80) as preview
    ORDER BY length(path)
    """
    
    results = neo4j.execute_query(query)
    
    for i, r in enumerate(results, 1):
        print(f"\n{i}. Позиция в цепочке: {r['position']}")
        print(f"   Order в БД: {r['order']}")
        print(f"   ID: {r['id']}")
        print(f"   Содержание: {r['preview']}...")
        
        # Проверка: позиция в цепочке должна совпадать с order - 1
        expected_order = r['position'] + 1
        if r['order'] == expected_order:
            print(f"   ✅ Порядок корректен (position={r['position']} → order={r['order']})")
        else:
            print(f"   ⚠️  ОШИБКА: ожидался order={expected_order}, получен order={r['order']}")
    
    # 3. Проверить обратную навигацию (кто ссылается на кого)
    print(f"\n{'='*100}")
    print("ПРОВЕРКА СВЯЗЕЙ NEXT (кто → кого)")
    print(f"{'='*100}")
    
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(p1:Paragraph)-[:NEXT]->(p2:Paragraph)
    RETURN p1.order as from_order,
           left(p1.content, 60) as from_preview,
           p2.order as to_order,
           left(p2.content, 60) as to_preview
    ORDER BY p1.order
    LIMIT 5
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nНайдено NEXT связей: {len(results)}")
    
    for r in results:
        arrow = "→"
        status = "✅" if r['to_order'] == r['from_order'] + 1 else "⚠️"
        print(f"\n{status} Параграф #{r['from_order']} {arrow} Параграф #{r['to_order']}")
        print(f"   От:  {r['from_preview']}...")
        print(f"   К:   {r['to_preview']}...")
    
    # 4. Найти разрывы в последовательности
    print(f"\n{'='*100}")
    print("ПОИСК РАЗРЫВОВ В ПОСЛЕДОВАТЕЛЬНОСТИ NEXT")
    print(f"{'='*100}")
    
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(p1:Paragraph)
    MATCH (s)-[:HAS_PARAGRAPH]->(p2:Paragraph)
    WHERE p1.order + 1 = p2.order
      AND NOT exists((p1)-[:NEXT]->(p2))
    RETURN s.number as section,
           p1.order as gap_after,
           p2.order as gap_before
    ORDER BY p1.order
    """
    
    results = neo4j.execute_query(query)
    
    if results:
        print(f"\n⚠️  НАЙДЕНО {len(results)} РАЗРЫВОВ:")
        for r in results:
            print(f"   Секция {r['section']}: нет связи между #{r['gap_after']} и #{r['gap_before']}")
    else:
        print("\n✅ Разрывов не обнаружено - все последовательные параграфы связаны NEXT!")
    
    # 5. Проверить последний параграф (без исходящего NEXT)
    print(f"\n{'='*100}")
    print("ПОСЛЕДНИЙ ПАРАГРАФ СЕКЦИИ")
    print(f"{'='*100}")
    
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(last:Paragraph)
    WHERE NOT exists((last)-[:NEXT]->())
    RETURN last.order as order,
           left(last.content, 100) as preview
    """
    
    result = neo4j.execute_query(query)
    
    if result:
        print(f"\n✅ Найден последний параграф (без исходящего NEXT):")
        print(f"   Order: {result[0]['order']}")
        print(f"   Содержание: {result[0]['preview']}...")
    else:
        print("\n⚠️  Последний параграф не найден или имеет исходящий NEXT!")
    
    # 6. Итоговая статистика
    print(f"\n{'='*100}")
    print("ИТОГОВАЯ СТАТИСТИКА")
    print(f"{'='*100}")
    
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
    WITH s, count(p) as total_paras
    MATCH (s)-[:HAS_PARAGRAPH]->(p2:Paragraph)-[:NEXT]->()
    WITH s, total_paras, count(p2) as paras_with_next
    RETURN s.number as section,
           s.title as title,
           total_paras,
           paras_with_next,
           (total_paras - paras_with_next) as without_next
    """
    
    result = neo4j.execute_query(query)
    
    if result:
        r = result[0]
        print(f"\nСекция: {r['section']} - {r['title']}")
        print(f"Всего параграфов: {r['total_paras']}")
        print(f"С исходящим NEXT: {r['paras_with_next']}")
        print(f"Без исходящего NEXT: {r['without_next']}")
        
        if r['without_next'] == 1:
            print(f"\n✅ КОРРЕКТНО: только 1 параграф без NEXT (последний)")
        else:
            print(f"\n⚠️  ВНИМАНИЕ: {r['without_next']} параграфов без NEXT")
    
    neo4j.close()
    
    print(f"\n{'='*100}")
    print("✅ ПРОВЕРКА ЗАВЕРШЕНА")
    print(f"{'='*100}\n")


if __name__ == '__main__':
    check_next_sequence()
