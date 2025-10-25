#!/usr/bin/env python3
"""
Визуализация полной цепочки NEXT для первой секции
"""
import yaml
from src.utils.neo4j_connection import Neo4jConnection


def visualize_next_chain():
    """Визуализировать цепочку NEXT"""
    
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
    print("ВИЗУАЛИЗАЦИЯ ЦЕПОЧКИ NEXT")
    print("=" * 100)
    
    # Получить всю цепочку через NEXT
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(first:Paragraph)
    WHERE NOT exists((first)<-[:NEXT]-())
    MATCH path = (first)-[:NEXT*0..]->(p:Paragraph)
    RETURN length(path) as position,
           p.order as db_order,
           left(p.content, 70) as preview
    ORDER BY length(path)
    """
    
    results = neo4j.execute_query(query)
    
    print(f"\nНайдено параграфов в цепочке: {len(results)}")
    print(f"\nПоследовательность NEXT:\n")
    
    print("Позиция | DB Order | Превью содержания")
    print("-" * 100)
    
    for r in results:
        status = "✅" if r['position'] + 1 == r['db_order'] else "⚠️"
        print(f"{status} {r['position']:3d}    | {r['db_order']:3d}      | {r['preview']}...")
    
    # Проверка целостности
    print(f"\n{'='*100}")
    print("ПРОВЕРКА ЦЕЛОСТНОСТИ")
    print(f"{'='*100}")
    
    expected_positions = set(range(len(results)))
    actual_positions = set(r['position'] for r in results)
    
    missing = expected_positions - actual_positions
    extra = actual_positions - expected_positions
    
    if not missing and not extra:
        print(f"\n✅ Цепочка полная и непрерывная!")
        print(f"   Все позиции от 0 до {len(results)-1} присутствуют")
    else:
        if missing:
            print(f"\n⚠️  Пропущенные позиции: {sorted(missing)}")
        if extra:
            print(f"\n⚠️  Лишние позиции: {sorted(extra)}")
    
    # Проверка соответствия position и db_order
    mismatches = [(r['position'], r['db_order']) for r in results if r['position'] + 1 != r['db_order']]
    
    if not mismatches:
        print(f"\n✅ Все position соответствуют db_order (position + 1 = db_order)")
    else:
        print(f"\n⚠️  Найдено {len(mismatches)} несоответствий:")
        for pos, order in mismatches[:5]:
            print(f"   position={pos} → ожидался order={pos+1}, получен order={order}")
    
    neo4j.close()
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    visualize_next_chain()
