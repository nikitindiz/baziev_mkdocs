#!/usr/bin/env python3
"""
Удалить параграфы и пересоздать их с новой логикой
"""
import yaml
from src.utils.neo4j_connection import Neo4jConnection


def clear_paragraphs():
    """Удалить все параграфы и их связи"""
    
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
    print("УДАЛЕНИЕ ПАРАГРАФОВ И ИХ СВЯЗЕЙ")
    print("=" * 100)
    
    # Проверить количество параграфов
    query = "MATCH (p:Paragraph) RETURN count(p) as count"
    result = neo4j.execute_query(query)
    para_count = result[0]['count'] if result else 0
    
    print(f"\nТекущее количество параграфов: {para_count}")
    
    if para_count == 0:
        print("\n✅ Параграфы отсутствуют, удаление не требуется")
        neo4j.close()
        return
    
    # Удалить все параграфы и их связи
    print(f"\n⚠️  Удаление {para_count} параграфов...")
    
    query = """
    MATCH (p:Paragraph)
    DETACH DELETE p
    """
    
    neo4j.execute_query(query)
    
    # Проверить результат
    query = "MATCH (p:Paragraph) RETURN count(p) as count"
    result = neo4j.execute_query(query)
    para_count = result[0]['count'] if result else 0
    
    if para_count == 0:
        print(f"\n✅ Все параграфы успешно удалены")
    else:
        print(f"\n⚠️  Осталось {para_count} параграфов")
    
    neo4j.close()
    
    print(f"\n{'='*100}\n")


if __name__ == '__main__':
    import sys
    
    print("\n⚠️  ВНИМАНИЕ: Эта операция удалит все параграфы из графа!")
    response = input("Продолжить? (yes/no): ")
    
    if response.lower() == 'yes':
        clear_paragraphs()
        print("\nТеперь запустите:")
        print("  python main.py import paragraphs")
    else:
        print("\nОперация отменена")
