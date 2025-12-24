#!/usr/bin/env python3
"""
Скрипт для создания недостающих связей CONTAINS_SYMBOL между формулами и символами.
Парсит LaTeX-код формул и создаёт связи с упомянутыми символами.
"""

import re
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USERNAME', os.getenv('NEO4J_USER'))
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

def extract_symbol_ids(latex_text):
    """Извлекает ID символов из LaTeX-кода формулы."""
    if not latex_text:
        return []
    
    # Ищем паттерн {{symbol:ID}}
    pattern = r'\{\{symbol:(\d+)\}\}'
    matches = re.findall(pattern, latex_text)
    return list(set(matches))  # Убираем дубликаты

def create_formula_symbol_links(driver):
    """Создаёт связи между формулами и символами."""
    
    with driver.session() as session:
        # Получаем все формулы с символами в LaTeX, но без связей
        result = session.run("""
            MATCH (f:Formula)
            WHERE f.latex CONTAINS '{{symbol:'
            RETURN f.id as formula_id, f.latex as latex
        """)
        
        formulas = list(result)
        print(f"📊 Найдено формул для обработки: {len(formulas)}")
        
        created_links = 0
        processed_formulas = 0
        formulas_with_links = 0
        errors = []
        
        for record in formulas:
            formula_id = record['formula_id']
            latex = record['latex']
            
            # Извлекаем ID символов
            symbol_ids = extract_symbol_ids(latex)
            
            if not symbol_ids:
                continue
            
            processed_formulas += 1
            
            # Проверяем, есть ли уже связи
            existing = session.run("""
                MATCH (f:Formula {id: $formula_id})-[:CONTAINS_SYMBOL]->(:Symbol)
                RETURN count(*) as link_count
            """, formula_id=formula_id).single()
            
            if existing and existing['link_count'] > 0:
                formulas_with_links += 1
                continue
            
            # Создаём связи для каждого символа
            for symbol_id in symbol_ids:
                try:
                    result = session.run("""
                        MATCH (f:Formula {id: $formula_id})
                        MATCH (s:Symbol {id: $symbol_id})
                        MERGE (f)-[:CONTAINS_SYMBOL]->(s)
                        RETURN f.id, s.id
                    """, formula_id=formula_id, symbol_id=symbol_id)
                    
                    if result.single():
                        created_links += 1
                        print(f"  ✓ Связь создана: Formula({formula_id}) → Symbol({symbol_id})")
                    
                except Exception as e:
                    error_msg = f"Ошибка для формулы {formula_id}, символ {symbol_id}: {e}"
                    errors.append(error_msg)
                    print(f"  ✗ {error_msg}")
        
        print(f"\n✨ Результаты:")
        print(f"  • Обработано формул: {processed_formulas}")
        print(f"  • Формул уже имели связи: {formulas_with_links}")
        print(f"  • Создано новых связей: {created_links}")
        
        if errors:
            print(f"\n⚠️ Ошибки ({len(errors)}):")
            for error in errors[:10]:  # Показываем первые 10
                print(f"  • {error}")

def main():
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("❌ Не заданы переменные окружения NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return
    
    print("🔧 Подключение к Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        print("🚀 Создание связей между формулами и символами...\n")
        create_formula_symbol_links(driver)
        print("\n✅ Готово!")
    finally:
        driver.close()

if __name__ == "__main__":
    main()
