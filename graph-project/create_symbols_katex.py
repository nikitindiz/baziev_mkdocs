#!/usr/bin/env python3
"""
Создание символов для формул с использованием KaTeX парсера.
Использует Node.js + KaTeX для точного анализа структуры формул.
"""

import sys
import os
import json
import hashlib
import subprocess
from datetime import datetime
from typing import List, Dict, Set

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.neo4j_connection import Neo4jConnection
from utils.config import load_config


def generate_symbol_id(latex: str) -> str:
    """Генерирует ID для символа на основе LaTeX."""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def create_katex_parser_script():
    """
    Создает Node.js скрипт для парсинга LaTeX формул через KaTeX.
    """
    script = """
const katex = require('katex');

// Читаем LaTeX из stdin
let latex = '';
process.stdin.on('data', chunk => latex += chunk);
process.stdin.on('end', () => {
    try {
        // Парсим LaTeX через KaTeX
        const parsed = katex.__parse(latex, {
            throwOnError: false,
            strict: false
        });
        
        // Извлекаем символы из дерева
        const symbols = new Set();
        
        function traverse(node) {
            if (!node) return;
            
            // Обрабатываем разные типы узлов
            switch (node.type) {
                case 'textord':
                case 'mathord':
                    // Обычные символы (переменные)
                    if (node.text && /^[a-zA-Z]$/.test(node.text)) {
                        symbols.add(node.text);
                    }
                    break;
                
                case 'atom':
                    // Атомарные символы
                    if (node.text) {
                        symbols.add(node.text);
                    }
                    break;
                
                case 'op':
                    // Операторы (sin, cos, log, etc.) - пропускаем
                    break;
                
                case 'ordgroup':
                case 'styling':
                    // Группы - обрабатываем рекурсивно
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(traverse);
                        } else {
                            traverse(node.body);
                        }
                    }
                    break;
                
                case 'supsub':
                    // Индексы и степени
                    if (node.base) traverse(node.base);
                    if (node.sub) {
                        // Нижний индекс
                        const subText = extractText(node.sub);
                        if (subText && node.base) {
                            const baseText = extractText(node.base);
                            if (baseText) {
                                symbols.add(baseText + '_' + subText);
                            }
                        }
                    }
                    if (node.sup) {
                        // Верхний индекс
                        const supText = extractText(node.sup);
                        if (supText && node.base) {
                            const baseText = extractText(node.base);
                            if (baseText) {
                                symbols.add(baseText + '^' + supText);
                            }
                        }
                    }
                    break;
                
                case 'accent':
                    // Акценты (штрихи и т.д.)
                    if (node.base) {
                        const baseText = extractText(node.base);
                        if (baseText) {
                            symbols.add(baseText + "'" );
                        }
                    }
                    break;
                
                case 'sqrt':
                case 'leftright':
                case 'middle':
                case 'delimsizing':
                    // Скобки, корни - обрабатываем содержимое
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(traverse);
                        } else {
                            traverse(node.body);
                        }
                    }
                    break;
                
                case 'genfrac':
                    // Дроби - обрабатываем числитель и знаменатель
                    if (node.numer) traverse(node.numer);
                    if (node.denom) traverse(node.denom);
                    break;
                
                default:
                    // Для всех остальных типов пытаемся обработать body
                    if (node.body) {
                        if (Array.isArray(node.body)) {
                            node.body.forEach(traverse);
                        } else {
                            traverse(node.body);
                        }
                    }
            }
        }
        
        function extractText(node) {
            if (!node) return '';
            
            if (node.text) return node.text;
            
            if (Array.isArray(node)) {
                return node.map(extractText).join('');
            }
            
            if (node.body) {
                if (Array.isArray(node.body)) {
                    return node.body.map(extractText).join('');
                }
                return extractText(node.body);
            }
            
            return '';
        }
        
        // Обрабатываем дерево
        if (Array.isArray(parsed)) {
            parsed.forEach(traverse);
        } else {
            traverse(parsed);
        }
        
        // Выводим результат
        console.log(JSON.stringify({
            success: true,
            symbols: Array.from(symbols)
        }));
        
    } catch (error) {
        console.log(JSON.stringify({
            success: false,
            error: error.message
        }));
    }
});
"""
    
    script_path = "/tmp/katex_parser.js"
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(script)
    
    return script_path


def parse_latex_with_katex(latex: str, script_path: str) -> List[str]:
    """
    Парсит LaTeX формулу через KaTeX и возвращает список символов.
    """
    try:
        # Запускаем Node.js скрипт
        result = subprocess.run(
            ['node', script_path],
            input=latex.encode('utf-8'),
            capture_output=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        # Парсим результат
        output = json.loads(result.stdout.decode('utf-8'))
        
        if output.get('success'):
            return output.get('symbols', [])
        else:
            return []
            
    except Exception as e:
        print(f"⚠️  Ошибка парсинга: {e}")
        return []


def check_katex_installed() -> bool:
    """Проверяет, установлен ли KaTeX через npm."""
    try:
        result = subprocess.run(
            ['node', '-e', 'require("katex")'],
            capture_output=True,
            timeout=2
        )
        return result.returncode == 0
    except:
        return False


def install_katex():
    """Устанавливает KaTeX через npm."""
    print("KaTeX не установлен. Устанавливаем...")
    try:
        subprocess.run(['npm', 'install', '-g', 'katex'], check=True)
        print("✓ KaTeX установлен")
        return True
    except Exception as e:
        print(f"❌ Не удалось установить KaTeX: {e}")
        return False


def process_formulas_with_katex(conn: Neo4jConnection, batch_size: int = 100):
    """
    Обрабатывает все формулы с помощью KaTeX.
    """
    print("=" * 80)
    print("Создание символов с использованием KaTeX")
    print("=" * 80)
    print()
    
    # Проверяем KaTeX
    if not check_katex_installed():
        if not install_katex():
            print("❌ Не удалось установить KaTeX. Прерываем.")
            return None
    
    print("✓ KaTeX доступен")
    print()
    
    # Создаем скрипт парсера
    parser_script = create_katex_parser_script()
    
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
        'formulas_failed': 0
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
            symbols = parse_latex_with_katex(latex, parser_script)
            
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
    
    try:
        # Обрабатываем формулы
        stats = process_formulas_with_katex(conn, batch_size=100)
        
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
            print("✅ Готово!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
