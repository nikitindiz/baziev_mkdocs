#!/usr/bin/env python3
"""
Ручная корректировка конкретных символов.
Использование: python manual_symbol_fix.py "старый_latex" "новый_latex"
"""

import sys
import os
import hashlib

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.neo4j_connection import Neo4jConnection
from utils.config import load_config


def generate_symbol_id(latex: str) -> str:
    """Генерирует ID для символа на основе LaTeX."""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def fix_symbol_manually(conn: Neo4jConnection, old_latex: str, new_latex: str):
    """
    Исправляет конкретный символ:
    1. Находит символ по старому latex
    2. Создает новый символ с правильным latex
    3. Переносит все связи
    4. Удаляет старый символ
    """
    
    # Находим старый символ
    find_query = """
    MATCH (s:Symbol {latex: $old_latex})
    RETURN s.id as symbol_id,
           elementId(s) as element_id,
           count{(f:Formula)-[:USES_SYMBOL]->(s)} as usage_count
    """
    
    result = conn.execute_query(find_query, {'old_latex': old_latex})
    
    if not result:
        print(f"❌ Символ `{old_latex}` не найден")
        return False
    
    old_symbol_id = result[0]['symbol_id']
    usage_count = result[0]['usage_count']
    
    print(f"✓ Найден символ `{old_latex}` (ID: {old_symbol_id})")
    print(f"  Используется в {usage_count} формулах")
    
    # Создаем новый символ
    new_symbol_id = generate_symbol_id(new_latex)
    
    create_query = """
    MERGE (s:Symbol {id: $new_id})
    ON CREATE SET 
        s.latex = $latex,
        s.description = "Исправлено вручную",
        s.auto_generated = true,
        s.source = "manual_fix",
        s.created_at = datetime()
    RETURN s.id as symbol_id
    """
    
    conn.execute_query(create_query, {
        'new_id': new_symbol_id,
        'latex': new_latex
    })
    
    print(f"✓ Создан новый символ `{new_latex}` (ID: {new_symbol_id})")
    
    # Переносим все связи
    transfer_query = """
    MATCH (f:Formula)-[old_r:USES_SYMBOL]->(old_s:Symbol {id: $old_id})
    MATCH (new_s:Symbol {id: $new_id})
    MERGE (f)-[:USES_SYMBOL]->(new_s)
    DELETE old_r
    WITH count(*) as transferred
    RETURN transferred
    """
    
    transfer_result = conn.execute_query(transfer_query, {
        'old_id': old_symbol_id,
        'new_id': new_symbol_id
    })
    
    transferred = transfer_result[0]['transferred'] if transfer_result else 0
    
    print(f"✓ Перенесено {transferred} связей")
    
    # Удаляем старый символ
    delete_query = """
    MATCH (s:Symbol {id: $old_id})
    DELETE s
    """
    
    conn.execute_query(delete_query, {'old_id': old_symbol_id})
    
    print(f"✓ Удален старый символ")
    print()
    
    return True


def main():
    """Основная функция."""
    if len(sys.argv) < 3:
        print("Использование: python manual_symbol_fix.py 'старый_latex' 'новый_latex'")
        print()
        print("Примеры:")
        print("  python manual_symbol_fix.py 'n_\\\\n' 'n_\\\\hbar'")
        print("  python manual_symbol_fix.py 'a_\\\\o' 'a_\\\\omega'")
        sys.exit(1)
    
    old_latex = sys.argv[1]
    new_latex = sys.argv[2]
    
    config = load_config()
    neo4j_config = config["neo4j"]
    conn = Neo4jConnection(
        uri=neo4j_config["uri"],
        user=neo4j_config["username"],
        password=neo4j_config["password"],
        database=neo4j_config.get("database", "neo4j")
    )
    
    print("=" * 80)
    print("Ручная корректировка символа")
    print("=" * 80)
    print(f"Старый: `{old_latex}`")
    print(f"Новый:  `{new_latex}`")
    print("=" * 80)
    print()
    
    try:
        success = fix_symbol_manually(conn, old_latex, new_latex)
        
        if success:
            print("✅ Готово!")
        else:
            print("❌ Не удалось исправить символ")
            sys.exit(1)
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
