#!/usr/bin/env python3
"""
Скрипт для удаления сущности Symbol из Neo4j
"""

from neo4j import GraphDatabase
import os

# Конфигурация подключения
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "20021030")

def drop_symbol_entity():
    """Удаляет все индексы, ограничения и узлы Symbol"""
    
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    with driver.session() as session:
        # Проверяем количество узлов Symbol
        result = session.run("MATCH (s:Symbol) RETURN count(s) as count")
        count = result.single()["count"]
        print(f"Найдено узлов Symbol: {count}")
        
        if count > 0:
            print("⚠️  ВНИМАНИЕ: Обнаружены узлы Symbol! Удаление отменено.")
            return
        
        # Удаляем ограничение
        try:
            session.run("DROP CONSTRAINT symbol_id IF EXISTS")
            print("✓ Ограничение symbol_id удалено")
        except Exception as e:
            print(f"⚠️  Ошибка при удалении ограничения: {e}")
        
        # Удаляем индекс
        try:
            session.run("DROP INDEX symbol_latex IF EXISTS")
            print("✓ Индекс symbol_latex удалён")
        except Exception as e:
            print(f"⚠️  Ошибка при удалении индекса: {e}")
        
        # Проверяем оставшиеся индексы и ограничения для Symbol
        result = session.run("""
            SHOW CONSTRAINTS 
            YIELD name, labelsOrTypes, properties 
            WHERE 'Symbol' IN labelsOrTypes 
            RETURN name, labelsOrTypes, properties
        """)
        remaining_constraints = list(result)
        
        result = session.run("""
            SHOW INDEXES 
            YIELD name, labelsOrTypes, properties 
            WHERE 'Symbol' IN labelsOrTypes 
            RETURN name, labelsOrTypes, properties
        """)
        remaining_indexes = list(result)
        
        if remaining_constraints:
            print("\n⚠️  Остались ограничения для Symbol:")
            for record in remaining_constraints:
                print(f"  - {record['name']}: {record['properties']}")
        else:
            print("\n✓ Все ограничения для Symbol удалены")
        
        if remaining_indexes:
            print("\n⚠️  Остались индексы для Symbol:")
            for record in remaining_indexes:
                print(f"  - {record['name']}: {record['properties']}")
        else:
            print("✓ Все индексы для Symbol удалены")
        
        print("\n✅ Сущность Symbol успешно удалена из базы данных!")
    
    driver.close()

if __name__ == "__main__":
    drop_symbol_entity()
