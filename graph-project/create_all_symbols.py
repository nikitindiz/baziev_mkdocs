#!/usr/bin/env python3
"""
Создание символов для ВСЕХ формул в графе Neo4j.
Обрабатывает все формулы, извлекает символы из LaTeX и создает связи.
"""

import sys
import os
import re
import hashlib
from datetime import datetime

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.neo4j_connection import Neo4jConnection
from utils.config import load_config


def generate_symbol_id(latex: str) -> str:
    """Генерирует ID для символа на основе LaTeX."""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def extract_symbols_from_latex(latex: str) -> list[str]:
    """
    Извлекает символы из LaTeX формулы.
    Возвращает список уникальных символов.
    """
    if not latex:
        return []
    
    symbols = set()
    
    # Убираем текстовые блоки
    latex = re.sub(r'\\text\{[^}]+\}', '', latex)
    latex = re.sub(r'\\mathrm\{[^}]+\}', '', latex)
    latex = re.sub(r'\\operatorname\{[^}]+\}', '', latex)
    
    # Убираем единицы измерения
    latex = re.sub(r'\\,?\\text\{[А-Яа-яA-Za-z]+\}', '', latex)
    
    # 1. Греческие буквы
    greek_letters = [
        r'\\alpha', r'\\beta', r'\\gamma', r'\\delta', r'\\epsilon', r'\\varepsilon',
        r'\\zeta', r'\\eta', r'\\theta', r'\\vartheta', r'\\iota', r'\\kappa',
        r'\\lambda', r'\\mu', r'\\nu', r'\\xi', r'\\pi', r'\\varpi', r'\\rho',
        r'\\varrho', r'\\sigma', r'\\varsigma', r'\\tau', r'\\upsilon', r'\\phi',
        r'\\varphi', r'\\chi', r'\\psi', r'\\omega',
        r'\\Gamma', r'\\Delta', r'\\Theta', r'\\Lambda', r'\\Xi', r'\\Pi',
        r'\\Sigma', r'\\Upsilon', r'\\Phi', r'\\Psi', r'\\Omega'
    ]
    
    for letter in greek_letters:
        # Греческие буквы с индексами
        pattern = letter + r"(?:_\{[^}]+\}|_[a-zA-Z0-9]|\^\{[^}]+\}|\^[a-zA-Z0-9])*"
        matches = re.findall(pattern, latex)
        symbols.update(matches)
    
    # 2. Переменные с индексами (включая штрихи)
    # Примеры: z_O'', n(O), a_{i}, v_{0}, E_{0}
    indexed_pattern = r"([a-zA-Z])(?:'*|_\{[^}]+\}|_[a-zA-Z0-9]|\^\{[^}]+\}|\^[a-zA-Z0-9]|\([^)]+\))+"
    indexed_matches = re.findall(indexed_pattern, latex)
    for match in indexed_matches:
        # Восстанавливаем полное выражение
        pos = latex.find(match)
        if pos != -1:
            # Ищем полное выражение начиная с этой позиции
            full_match = match
            rest = latex[pos + len(match):]
            
            # Добавляем штрихи, индексы и скобки
            while rest and (rest[0] == "'" or rest.startswith('_') or rest.startswith('^') or rest.startswith('(')):
                if rest[0] == "'":
                    full_match += "'"
                    rest = rest[1:]
                elif rest.startswith('_') or rest.startswith('^'):
                    if len(rest) > 1 and rest[1] == '{':
                        # Найти закрывающую скобку
                        closing = rest.find('}')
                        if closing != -1:
                            full_match += rest[:closing+1]
                            rest = rest[closing+1:]
                        else:
                            break
                    elif len(rest) >= 2:
                        full_match += rest[:2]
                        rest = rest[2:]
                    else:
                        break
                elif rest.startswith('('):
                    closing = rest.find(')')
                    if closing != -1:
                        full_match += rest[:closing+1]
                        rest = rest[closing+1:]
                    else:
                        break
                else:
                    break
            
            if len(full_match) > 1:  # Только если есть индексы/штрихи
                symbols.add(full_match)
    
    # 3. Простые переменные (одна буква)
    simple_vars = re.findall(r'\b([a-zA-Z])\b', latex)
    for var in simple_vars:
        # Проверяем, что это не часть команды LaTeX
        if not re.search(r'\\[a-zA-Z]*' + var, latex):
            symbols.add(var)
    
    # 4. Специальные символы
    special_symbols = [
        r'\\odot', r'\\oplus', r'\\otimes', r'\\infty', r'\\partial',
        r'\\nabla', r'\\hbar', r'\\ell', r'\\wp', r'\\Re', r'\\Im'
    ]
    
    for symbol in special_symbols:
        if symbol in latex:
            symbols.add(symbol)
    
    # Фильтруем
    filtered_symbols = set()
    for symbol in symbols:
        # Убираем пустые и слишком короткие
        if not symbol or len(symbol.strip()) == 0:
            continue
        
        # Убираем числа
        if symbol.isdigit():
            continue
            
        filtered_symbols.add(symbol)
    
    return sorted(list(filtered_symbols))


def create_symbol_if_not_exists(conn: Neo4jConnection, latex: str, description: str, source: str) -> str:
    """
    Создает символ в графе, если он не существует.
    Возвращает symbol_id.
    """
    symbol_id = generate_symbol_id(latex)
    
    query = """
    MERGE (s:Symbol {id: $symbol_id})
    ON CREATE SET 
        s.latex = $latex,
        s.description = $description,
        s.auto_generated = true,
        s.source = $source,
        s.created_at = datetime()
    RETURN s.id as symbol_id
    """
    
    result = conn.execute_query(query, {
        'symbol_id': symbol_id,
        'latex': latex,
        'description': description,
        'source': source
    })
    
    return symbol_id


def link_formula_to_symbol(conn: Neo4jConnection, formula_id: str, symbol_id: str):
    """Создает связь USES_SYMBOL между формулой и символом."""
    query = """
    MATCH (f:Formula {id: $formula_id})
    MATCH (s:Symbol {id: $symbol_id})
    MERGE (f)-[:USES_SYMBOL]->(s)
    """
    
    conn.execute_query(query, {
        'formula_id': formula_id,
        'symbol_id': symbol_id
    })


def process_all_formulas(conn: Neo4jConnection, batch_size: int = 100):
    """
    Обрабатывает все формулы в графе.
    """
    print("=" * 80)
    print("Создание символов для ВСЕХ формул в графе")
    print("=" * 80)
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
    
    # Получаем формулы батчами
    stats = {
        'processed': 0,
        'formulas_with_symbols': 0,
        'formulas_without_symbols': 0,
        'symbols_created': set(),
        'links_created': 0,
        'formulas_skipped': []
    }
    
    skip = 0
    
    while skip < total_formulas:
        # Получаем батч формул
        query = """
        MATCH (f:Formula)
        OPTIONAL MATCH (p:Paragraph)-[:CONTAINS_FORMULA]->(f)
        OPTIONAL MATCH (s:Section)-[:CONTAINS_PARAGRAPH]->(p)
        RETURN f.id as formula_id, 
               f.latex as latex,
               s.title as section_title
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
            section_title = record.get('section_title', 'Неизвестный раздел')
            
            stats['processed'] += 1
            
            # Извлекаем символы
            symbols = extract_symbols_from_latex(latex)
            
            if not symbols:
                stats['formulas_without_symbols'] += 1
                stats['formulas_skipped'].append({
                    'id': formula_id,
                    'latex': latex,
                    'section': section_title
                })
                continue
            
            stats['formulas_with_symbols'] += 1
            
            # Создаем символы и связи
            for symbol_latex in symbols:
                symbol_id = create_symbol_if_not_exists(
                    conn,
                    latex=symbol_latex,
                    description="Автоматически извлечено из формул",
                    source="auto_extraction"
                )
                
                stats['symbols_created'].add(symbol_id)
                
                # Создаем связь
                link_formula_to_symbol(conn, formula_id, symbol_id)
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
    
    log_file = os.path.join(log_dir, "all_symbols_extraction.md")
    
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write("# Автоматическое создание символов для всех формул\n\n")
        f.write(f"Дата: {datetime.now().isoformat()}\n\n")
        
        f.write("## Статистика\n\n")
        f.write(f"- Всего обработано формул: {stats['processed']}\n")
        f.write(f"- Формул с извлеченными символами: {stats['formulas_with_symbols']}\n")
        f.write(f"- Формул без символов: {stats['formulas_without_symbols']}\n")
        f.write(f"- Создано уникальных символов: {len(stats['symbols_created'])}\n")
        f.write(f"- Создано связей USES_SYMBOL: {stats['links_created']}\n\n")
        
        if stats['formulas_skipped']:
            f.write(f"## Формулы без символов ({len(stats['formulas_skipped'])})\n\n")
            for item in stats['formulas_skipped'][:50]:  # Первые 50
                f.write(f"### ID: `{item['id']}`\n")
                f.write(f"- **LaTeX**: `{item['latex']}`\n")
                f.write(f"- **Раздел**: {item['section']}\n\n")
            
            if len(stats['formulas_skipped']) > 50:
                f.write(f"*...и ещё {len(stats['formulas_skipped']) - 50} формул*\n\n")
    
    return log_file


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
        # Обрабатываем все формулы
        stats = process_all_formulas(conn, batch_size=100)
        
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
        print("✅ Готово!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
