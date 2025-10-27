#!/usr/bin/env python3
"""
Создание символов для формул с использованием KaTeX парсера (Node.js).
"""

import sys
import os
import json
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.neo4j_connection import Neo4jConnection
from utils.config import load_config


def generate_symbol_id(latex: str) -> str:
    """Генерирует ID для символа на основе LaTeX."""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def parse_latex_with_katex(latex: str, parser_path: str) -> list:
    """
    Парсит LaTeX формулу через Node.js KaTeX парсер.
    """
    try:
        result = subprocess.run(
            ['node', parser_path, latex],
            capture_output=True,
            timeout=5,
            cwd=os.path.dirname(parser_path)
        )
        
        if result.returncode != 0:
            return []
        
        output = json.loads(result.stdout.decode('utf-8'))
        
        if output.get('success'):
            return output.get('symbols', [])
        else:
            return []
            
    except Exception as e:
        return []


def process_formulas(conn: Neo4jConnection, parser_path: str, batch_size: int = 100):
    """
    Обрабатывает все формулы с помощью KaTeX парсера.
    """
    print("=" * 80)
    print("Создание символов с использованием KaTeX парсера")
    print("=" * 80)
    print()
    
    # Проверяем парсер
    if not os.path.exists(parser_path):
        print(f"❌ Парсер не найден: {parser_path}")
        return None
    
    print(f"✓ Используем парсер: {parser_path}")
    print()
    
    # Получаем общее количество формул
    count_query = """
    MATCH (f:Formula)
    RETURN count(f) as total
    """
    total_result = conn.execute_query(count_query)
    total_formulas = total_result[0]['total'] if total_result else 0
    
    print(f"Всего формул в графе: {total_formulas}")
    print()
    
    # Статистика
    stats = {
        'processed': 0,
        'formulas_with_symbols': 0,
        'formulas_without_symbols': 0,
        'symbols_created': set(),
        'links_created': 0,
        'formulas_failed': []
    }
    
    skip = 0
    
    while skip < total_formulas:
        # Получаем батч формул
        query = """
        MATCH (f:Formula)
        RETURN f.id as formula_id, 
               f.latex as latex
        ORDER BY f.id
        SKIP $skip
        LIMIT $limit
        """
        
        batch = conn.execute_query(query, {'skip': skip, 'limit': batch_size})
        
        if not batch:
            break
        
        for record in batch:
            formula_id = record['formula_id']
            latex = record['latex']
            
            stats['processed'] += 1
            
            # Парсим через KaTeX
            symbols = parse_latex_with_katex(latex, parser_path)
            
            if not symbols:
                stats['formulas_without_symbols'] += 1
                continue
            
            stats['formulas_with_symbols'] += 1
            
            # Создаем символы и связи
            for symbol_latex in symbols:
                symbol_id = generate_symbol_id(symbol_latex)
                
                # Создаем символ
                create_query = """
                MERGE (s:Symbol {id: $symbol_id})
                ON CREATE SET 
                    s.latex = $latex,
                    s.description = "Извлечено через KaTeX парсер",
                    s.auto_generated = true,
                    s.source = "katex_parser",
                    s.created_at = datetime()
                """
                
                conn.execute_query(create_query, {
                    'symbol_id': symbol_id,
                    'latex': symbol_latex
                })
                
                stats['symbols_created'].add(symbol_id)
                
                # Создаем связь
                link_query = """
                MATCH (f:Formula {id: $formula_id})
                MATCH (s:Symbol {id: $symbol_id})
                MERGE (f)-[:USES_SYMBOL]->(s)
                """
                
                conn.execute_query(link_query, {
                    'formula_id': formula_id,
                    'symbol_id': symbol_id
                })
                
                stats['links_created'] += 1
            
            # Прогресс
            if stats['processed'] % 100 == 0:
                print(f"Обработано {stats['processed']}/{total_formulas} формул...")
        
        skip += batch_size
    
    return stats


def save_log(stats: dict):
    """Сохраняет лог обработки."""
    log_dir = "/Users/electrino/work/vibed/baziev_mkdocs/fixes-required"
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "katex_symbols_extraction.md")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# Создание символов через KaTeX парсер\n\n")
        f.write(f"Дата: {datetime.now().isoformat()}\n\n")
        
        f.write("## Статистика\n\n")
        f.write(f"- Всего обработано формул: {stats['processed']}\n")
        f.write(f"- Формул с извлеченными символами: {stats['formulas_with_symbols']}\n")
        f.write(f"- Формул без символов: {stats['formulas_without_symbols']}\n")
        f.write(f"- Создано уникальных символов: {len(stats['symbols_created'])}\n")
        f.write(f"- Создано связей USES_SYMBOL: {stats['links_created']}\n\n")
    
    return log_file


def main():
    """Основная функция."""
    # Путь к парсеру
    parser_path = os.path.join(
        os.path.dirname(__file__),
        'latex-parser',
        'index.js'
    )
    
    config = load_config()
    neo4j_config = config["neo4j"]
    conn = Neo4jConnection(
        uri=neo4j_config["uri"],
        user=neo4j_config["username"],
        password=neo4j_config["password"],
        database=neo4j_config.get("database", "neo4j")
    )
    
    try:
        # Обрабатываем формулы
        stats = process_formulas(conn, parser_path, batch_size=100)
        
        if stats:
            print()
            print("=" * 80)
            print("Результаты:")
            print(f"  Обработано формул: {stats['processed']}")
            print(f"  Формул с символами: {stats['formulas_with_symbols']}")
            print(f"  Формул без символов: {stats['formulas_without_symbols']}")
            print(f"  Создано уникальных символов: {len(stats['symbols_created'])}")
            print(f"  Создано связей USES_SYMBOL: {stats['links_created']}")
            print("=" * 80)
            print()
            
            # Сохраняем лог
            log_file = save_log(stats)
            print(f"Лог сохранён в: {log_file}")
            print()
            print("✅ Готово!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
