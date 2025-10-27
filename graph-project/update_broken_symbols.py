#!/usr/bin/env python3
"""
Обновление существующих символов в графе.
Пересоздает символы только для формул, которые имеют некорректные символы.
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
    Извлекает символы из LaTeX формулы (улучшенная версия).
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
        pattern = letter + r"(?:_\{[^}]+\}|_\\[a-zA-Z]+|_[a-zA-Z0-9]|\^\{[^}]+\}|\^\\[a-zA-Z]+|\^[a-zA-Z0-9])*"
        matches = re.findall(pattern, latex)
        symbols.update(matches)
    
    # 2. Переменные с индексами (включая штрихи)
    # Примеры: z_O'', n(O), a_{i}, v_{0}, E_{0}, n_\hbar, a_\omega
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
                        # Найти закрывающую скобку: _{...}
                        closing = rest.find('}')
                        if closing != -1:
                            full_match += rest[:closing+1]
                            rest = rest[closing+1:]
                        else:
                            break
                    elif len(rest) > 1 and rest[1] == '\\':
                        # LaTeX команда после _ или ^: _\hbar, _\omega, etc.
                        # Ищем полную команду (буквы после \)
                        cmd_match = re.match(r'^[_^](\\[a-zA-Z]+)', rest)
                        if cmd_match:
                            cmd = cmd_match.group(0)
                            full_match += cmd
                            rest = rest[len(cmd):]
                        else:
                            # Просто _ или ^ без продолжения
                            break
                    elif len(rest) >= 2:
                        # Одиночный символ после _ или ^: _i, ^2
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
    
    # 4. Специальные символы (как самостоятельные, так и в индексах)
    special_symbols = [
        r'\\hbar', r'\\ell', r'\\wp',
        r'\\odot', r'\\oplus', r'\\otimes', r'\\infty', r'\\partial',
        r'\\nabla', r'\\Re', r'\\Im',
        r'\\prime', r'\\ast', r'\\star', r'\\circ', r'\\bullet',
        r'\\cdot', r'\\times', r'\\div'
    ]
    
    for symbol in special_symbols:
        # Проверяем, есть ли символ как самостоятельный (не после _ или ^)
        # Используем негативный lookbehind для проверки, что перед символом нет _ или ^
        pattern = r'(?<!_)(?<!\^)' + symbol + r'(?!\\[a-zA-Z])'
        if re.search(pattern, latex):
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
        
        # Убираем символы, заканчивающиеся на _ или ^ или \ (некорректные)
        if symbol.endswith('_') or symbol.endswith('^') or symbol.endswith('\\'):
            continue
            
        filtered_symbols.add(symbol)
    
    return sorted(list(filtered_symbols))


def find_formulas_with_broken_symbols(conn: Neo4jConnection) -> list:
    """
    Находит формулы, которые имеют связь с некорректными символами
    (заканчиваются на _, ^, или \).
    """
    query = """
    MATCH (f:Formula)-[:USES_SYMBOL]->(s:Symbol)
    WHERE s.latex ENDS WITH '_' 
       OR s.latex ENDS WITH '^'
       OR s.latex ENDS WITH '\\\\'
    RETURN DISTINCT f.id as formula_id,
           f.latex as formula_latex,
           collect(DISTINCT s.latex) as broken_symbols
    ORDER BY f.id
    """
    
    return conn.execute_query(query)


def recreate_symbols_for_formula(conn: Neo4jConnection, formula_id: str, formula_latex: str):
    """
    Пересоздает символы для конкретной формулы:
    1. Удаляет все старые связи USES_SYMBOL
    2. Извлекает символы заново
    3. Создает новые символы и связи
    """
    
    # Удаляем старые связи
    delete_query = """
    MATCH (f:Formula {id: $formula_id})-[r:USES_SYMBOL]->()
    DELETE r
    """
    conn.execute_query(delete_query, {'formula_id': formula_id})
    
    # Извлекаем символы
    symbols = extract_symbols_from_latex(formula_latex)
    
    if not symbols:
        return 0
    
    # Создаем новые символы и связи
    links_created = 0
    for symbol_latex in symbols:
        symbol_id = generate_symbol_id(symbol_latex)
        
        # Создаем символ
        create_query = """
        MERGE (s:Symbol {id: $symbol_id})
        ON CREATE SET 
            s.latex = $latex,
            s.description = "Автоматически извлечено из формул (обновлено)",
            s.auto_generated = true,
            s.source = "auto_extraction_v2",
            s.created_at = datetime()
        """
        
        conn.execute_query(create_query, {
            'symbol_id': symbol_id,
            'latex': symbol_latex
        })
        
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
        
        links_created += 1
    
    return links_created


def cleanup_orphaned_symbols(conn: Neo4jConnection) -> int:
    """Удаляет символы, которые больше не используются ни одной формулой."""
    query = """
    MATCH (s:Symbol)
    WHERE NOT EXISTS {(f:Formula)-[:USES_SYMBOL]->(s)}
    WITH s
    DELETE s
    RETURN count(*) as deleted
    """
    
    result = conn.execute_query(query)
    return result[0]['deleted'] if result else 0


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
    print("Обновление некорректных символов")
    print("=" * 80)
    print()
    
    try:
        # Находим формулы с проблемными символами
        formulas_to_fix = find_formulas_with_broken_symbols(conn)
        
        print(f"Найдено формул с некорректными символами: {len(formulas_to_fix)}")
        print()
        
        if not formulas_to_fix:
            print("✅ Все символы корректны!")
            return
        
        # Статистика
        fixed_count = 0
        total_links = 0
        
        for i, formula in enumerate(formulas_to_fix, 1):
            formula_id = formula['formula_id']
            formula_latex = formula['formula_latex']
            broken_symbols = formula['broken_symbols']
            
            if i % 50 == 0:
                print(f"Обработано {i}/{len(formulas_to_fix)} формул...")
            
            # Пересоздаем символы
            links_created = recreate_symbols_for_formula(conn, formula_id, formula_latex)
            
            fixed_count += 1
            total_links += links_created
        
        print()
        print("=" * 80)
        print("Результаты:")
        print(f"  Исправлено формул: {fixed_count}")
        print(f"  Создано новых связей: {total_links}")
        print("=" * 80)
        print()
        
        # Удаляем потерянные символы
        print("Удаление неиспользуемых символов...")
        deleted = cleanup_orphaned_symbols(conn)
        print(f"✓ Удалено неиспользуемых символов: {deleted}")
        print()
        
        print("✅ Готово!")
        
    finally:
        conn.close()


if __name__ == "__main__":
    main()
