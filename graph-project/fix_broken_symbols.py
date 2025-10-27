#!/usr/bin/env python3
"""
Исправление некорректно распознанных символов.
Находит символы, заканчивающиеся на _ или ^ без продолжения, и пытается их исправить.
"""

import sys
import os
import hashlib
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.neo4j_connection import Neo4jConnection
from utils.config import load_config


def generate_symbol_id(latex: str) -> str:
    """Генерирует ID для символа на основе LaTeX."""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def find_broken_symbols(conn: Neo4jConnection) -> list:
    """
    Находит символы, которые выглядят неполными:
    - Заканчиваются на _ или ^ или \
    """
    query = """
    MATCH (s:Symbol)
    WHERE s.latex ENDS WITH '_' 
       OR s.latex ENDS WITH '^'
       OR s.latex ENDS WITH '\\\\'
    OPTIONAL MATCH (f:Formula)-[:USES_SYMBOL]->(s)
    RETURN s.id as symbol_id,
           s.latex as symbol_latex,
           elementId(s) as element_id,
           collect(DISTINCT f.id) as formula_ids,
           collect(DISTINCT f.latex)[0..3] as sample_formulas
    ORDER BY s.latex
    """
    
    return conn.execute_query(query)


def find_formulas_with_symbol(conn: Neo4jConnection, symbol_id: str) -> list:
    """Находит все формулы, использующие данный символ."""
    query = """
    MATCH (f:Formula)-[:USES_SYMBOL]->(s:Symbol {id: $symbol_id})
    RETURN f.id as formula_id,
           f.latex as formula_latex
    """
    
    return conn.execute_query(query, {'symbol_id': symbol_id})


def extract_correct_symbol(formula_latex: str, broken_symbol: str) -> str:
    """
    Пытается извлечь правильный символ из формулы.
    Ищет паттерн broken_symbol + продолжение.
    """
    import re
    
    # Экранируем спецсимволы для regex
    escaped = re.escape(broken_symbol)
    
    # Ищем паттерн: broken_symbol + {что-то} или broken_symbol + команда LaTeX
    patterns = [
        # n_\hbar, n_\omega и т.д.
        escaped + r'\\[a-zA-Z]+',
        # n_{что-то}
        escaped + r'\{[^}]+\}',
        # n_x (один символ)
        escaped + r'[a-zA-Z0-9]',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, formula_latex)
        if matches:
            # Берем самое длинное совпадение
            return max(matches, key=len)
    
    return None


def fix_symbol(conn: Neo4jConnection, old_symbol_id: str, new_symbol_latex: str) -> dict:
    """
    Исправляет символ:
    1. Создает новый символ с правильным latex
    2. Переносит все связи со старого на новый
    3. Удаляет старый символ
    """
    new_symbol_id = generate_symbol_id(new_symbol_latex)
    
    # Создаем новый символ
    create_query = """
    MERGE (s:Symbol {id: $new_id})
    ON CREATE SET 
        s.latex = $latex,
        s.description = "Исправлено автоматически",
        s.auto_generated = true,
        s.source = "auto_fix",
        s.created_at = datetime()
    RETURN s.id as symbol_id
    """
    
    conn.execute_query(create_query, {
        'new_id': new_symbol_id,
        'latex': new_symbol_latex
    })
    
    # Переносим все связи
    transfer_query = """
    MATCH (f:Formula)-[old_r:USES_SYMBOL]->(old_s:Symbol {id: $old_id})
    MATCH (new_s:Symbol {id: $new_id})
    MERGE (f)-[:USES_SYMBOL]->(new_s)
    DELETE old_r
    WITH old_s, count(*) as transferred
    RETURN transferred
    """
    
    result = conn.execute_query(transfer_query, {
        'old_id': old_symbol_id,
        'new_id': new_symbol_id
    })
    
    transferred = result[0]['transferred'] if result else 0
    
    # Удаляем старый символ
    delete_query = """
    MATCH (s:Symbol {id: $old_id})
    DELETE s
    """
    
    conn.execute_query(delete_query, {'old_id': old_symbol_id})
    
    return {
        'old_id': old_symbol_id,
        'new_id': new_symbol_id,
        'new_latex': new_symbol_latex,
        'transferred': transferred
    }


def main():
    """Основная функция."""
    config = load_config()
    neo4j_config = config["neo4j"]
    conn = Neo4jConnection(
        uri=neo4j_config["uri"],
        user=neo4j_config["username"],
        password=neo4j_config["password"],
        database=neo4j_config.get("database", "neo4j")
    )
    
    print("=" * 80)
    print("Исправление некорректных символов")
    print("=" * 80)
    print()
    
    try:
        # Находим проблемные символы
        broken_symbols = find_broken_symbols(conn)
        
        print(f"Найдено проблемных символов: {len(broken_symbols)}")
        print()
        
        if not broken_symbols:
            print("✅ Все символы корректны!")
            return
        
        # Статистика
        fixed_count = 0
        skipped_count = 0
        fixes = []
        
        for symbol in broken_symbols:
            symbol_id = symbol['symbol_id']
            symbol_latex = symbol['symbol_latex']
            formula_ids = symbol['formula_ids']
            sample_formulas = symbol['sample_formulas']
            
            print(f"Проблемный символ: `{symbol_latex}` (используется в {len(formula_ids)} формулах)")
            
            if not sample_formulas or not sample_formulas[0]:
                print("  ⚠️  Нет формул для анализа, пропускаем")
                skipped_count += 1
                continue
            
            # Пытаемся извлечь правильный символ
            correct_symbol = None
            for formula_latex in sample_formulas:
                if formula_latex:
                    correct_symbol = extract_correct_symbol(formula_latex, symbol_latex)
                    if correct_symbol:
                        break
            
            if correct_symbol and correct_symbol != symbol_latex:
                print(f"  ✓ Найден правильный символ: `{correct_symbol}`")
                
                # Исправляем
                fix_result = fix_symbol(conn, symbol_id, correct_symbol)
                fixed_count += 1
                fixes.append(fix_result)
                
                print(f"    Перенесено связей: {fix_result['transferred']}")
            else:
                print(f"  ⚠️  Не удалось определить правильный символ")
                skipped_count += 1
            
            print()
        
        # Итоговая статистика
        print("=" * 80)
        print("Результаты:")
        print(f"  Исправлено символов: {fixed_count}")
        print(f"  Пропущено: {skipped_count}")
        print("=" * 80)
        print()
        
        # Сохраняем лог
        if fixes:
            log_dir = "/Users/electrino/work/vibed/baziev_mkdocs/fixes-required"
            os.makedirs(log_dir, exist_ok=True)
            
            log_file = os.path.join(log_dir, "symbol_fixes.md")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("# Исправление некорректных символов\n\n")
                f.write(f"Дата: {datetime.now().isoformat()}\n\n")
                f.write("## Исправленные символы\n\n")
                
                for fix in fixes:
                    f.write(f"### `{fix['new_latex']}`\n")
                    f.write(f"- **Старый ID**: `{fix['old_id']}`\n")
                    f.write(f"- **Новый ID**: `{fix['new_id']}`\n")
                    f.write(f"- **Перенесено связей**: {fix['transferred']}\n\n")
            
            print(f"Лог сохранён в: {log_file}")
        
        print("✅ Готово!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
