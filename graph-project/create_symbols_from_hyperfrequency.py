"""
Создание символов для формул из разделов гиперчастотной механики
"""
import re
import json
import hashlib
import sys
from pathlib import Path
from typing import Set, List, Dict, Tuple

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.neo4j_connection import Neo4jConnection
from src.utils.config import load_config

# Список разделов гиперчастотной механики
HYPERFREQUENCY_SECTIONS = [
    'chapter_глава-i-система-новейших-фундаментальных-открытий_1-гиперчастотная-механика-или-механика-микромира',
    'chapter_глава-i-система-новейших-фундаментальных-открытий_5-гиперчастотная-механика-и-истинный-абсолютный-нуль',
    'chapter_глава-vii-физика-солнца_28-гиперчастотные-и-энергетические-параметры-солнечной-плазмы-в-функции-от-глубины-н',
    'chapter_приложение-1-гиперчастотные-параметры-некоторых-газов-в-нормальных-условиях'
]

def generate_symbol_id(latex: str) -> str:
    """Генерация уникального ID для символа на основе LaTeX"""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def extract_symbols_from_latex(latex: str) -> Set[str]:
    """
    Извлечение символов из LaTeX выражения.
    Возвращает множество базовых символов (переменных, констант).
    """
    if not latex:
        return set()
    
    symbols = set()
    
    # Шаг 1: Удаляем текстовые команды
    latex_clean = re.sub(r'\\text\{[^}]*\}', '', latex)
    latex_clean = re.sub(r'\\mathrm\{[^}]*\}', '', latex_clean)
    
    # Шаг 2: Греческие буквы (\alpha, \beta, etc.)
    greek_pattern = r'\\(alpha|beta|gamma|delta|epsilon|varepsilon|zeta|eta|theta|vartheta|iota|kappa|lambda|mu|nu|xi|pi|rho|varrho|sigma|varsigma|tau|upsilon|phi|varphi|chi|psi|omega|Gamma|Delta|Theta|Lambda|Xi|Pi|Sigma|Upsilon|Phi|Psi|Omega)'
    for match in re.finditer(greek_pattern, latex_clean):
        symbols.add('\\' + match.group(1))
    
    # Шаг 3: Индексированные переменные (A_0, v_i, etc.)
    indexed_pattern = r'([A-Za-z])_(?:\{([^}]+)\}|([A-Za-z0-9]+))'
    for match in re.finditer(indexed_pattern, latex_clean):
        base = match.group(1)
        index = match.group(2) or match.group(3)
        symbols.add(f'{base}_{{{index}}}')
    
    # Шаг 4: Простые переменные (одиночные латинские буквы)
    # Исключаем те, что уже были найдены с индексами
    simple_vars = re.findall(r'\b([A-Za-z])\b', latex_clean)
    for var in simple_vars:
        # Проверяем, что это не часть команды LaTeX
        if not re.search(r'\\' + var, latex):
            # Проверяем, что нет индекса после этой буквы
            if not re.search(rf'{var}_', latex_clean):
                symbols.add(var)
    
    # Шаг 5: Специальные символы математики
    special_symbols = [
        r'\\odot',  # Солнце
        r'\\oplus', # Земля
        r'\\infty',
        r'\\degree'
    ]
    for special in special_symbols:
        if special in latex:
            symbols.add(special)
    
    # Шаг 6: Индексы с греческими буквами
    greek_indexed = r'\\(alpha|beta|gamma|delta|epsilon|mu|nu|tau|sigma|phi|psi|omega)_(?:\{([^}]+)\}|([A-Za-z0-9]+))'
    for match in re.finditer(greek_indexed, latex_clean):
        greek = '\\' + match.group(1)
        index = match.group(2) or match.group(3)
        symbols.add(f'{greek}_{{{index}}}')
    
    return symbols


def get_formulas_from_sections(conn: Neo4jConnection, section_ids: List[str]) -> List[Dict]:
    """Получить все формулы из указанных разделов"""
    query = """
    UNWIND $section_ids AS sec_id
    MATCH (sec:Section {id: sec_id})-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
    WHERE f.latex IS NOT NULL AND f.latex <> ''
    RETURN DISTINCT f.id as formula_id, f.latex as latex, sec.title as section_title
    ORDER BY sec.title, f.id
    """
    result = conn.execute_query(query, {'section_ids': section_ids})
    return result


def create_symbol_if_not_exists(conn: Neo4jConnection, latex: str, description: str = "", metadata: Dict = None) -> str:
    """Создать символ в графе, если его нет"""
    symbol_id = generate_symbol_id(latex)
    
    if metadata is None:
        metadata = {}
    
    metadata_json = json.dumps(metadata)
    
    query = """
    MERGE (s:Symbol {id: $id})
    ON CREATE SET 
        s.latex = $latex,
        s.description = $description,
        s.metadata = $metadata
    RETURN s.id as id
    """
    
    conn.execute_write(query, {
        'id': symbol_id,
        'latex': latex,
        'description': description,
        'metadata': metadata_json
    })
    
    return symbol_id


def link_formula_to_symbol(conn: Neo4jConnection, formula_id: str, symbol_id: str):
    """Создать связь USES_SYMBOL между формулой и символом"""
    query = """
    MATCH (f:Formula {id: $formula_id})
    MATCH (s:Symbol {id: $symbol_id})
    MERGE (f)-[:USES_SYMBOL]->(s)
    """
    
    conn.execute_write(query, {
        'formula_id': formula_id,
        'symbol_id': symbol_id
    })


def main():
    print("=" * 80)
    print("Создание символов для формул гиперчастотной механики")
    print("=" * 80)
    
    config = load_config()
    neo4j_config = config["neo4j"]
    conn = Neo4jConnection(
        uri=neo4j_config["uri"],
        user=neo4j_config["username"],
        password=neo4j_config["password"],
        database=neo4j_config.get("database", "neo4j")
    )
    
    # Создаём папку для логов ошибок
    fixes_dir = Path('/Users/electrino/work/vibed/baziev_mkdocs/fixes-required')
    fixes_dir.mkdir(exist_ok=True)
    
    log_file = fixes_dir / 'hyperfrequency_symbols_issues.md'
    
    issues = []
    issues.append("# Проблемы при создании символов для гиперчастотной механики\n\n")
    issues.append(f"Дата: {Path(__file__).stat().st_mtime}\n\n")
    
    # Получаем формулы
    print(f"\nПолучение формул из {len(HYPERFREQUENCY_SECTIONS)} разделов...")
    formulas = get_formulas_from_sections(conn, HYPERFREQUENCY_SECTIONS)
    print(f"Найдено формул: {len(formulas)}")
    
    # Статистика
    total_symbols_created = 0
    total_links_created = 0
    symbol_cache = {}  # latex -> symbol_id
    
    issues.append(f"## Обработано формул: {len(formulas)}\n\n")
    
    # Обрабатываем каждую формулу
    for idx, formula_data in enumerate(formulas, 1):
        formula_id = formula_data['formula_id']
        latex = formula_data['latex']
        section = formula_data['section_title']
        
        if idx % 50 == 0:
            print(f"Обработано {idx}/{len(formulas)} формул...")
        
        # Извлекаем символы
        symbols = extract_symbols_from_latex(latex)
        
        if not symbols:
            issues.append(f"### ⚠️ Формула без символов\n")
            issues.append(f"- **ID**: `{formula_id}`\n")
            issues.append(f"- **LaTeX**: `{latex}`\n")
            issues.append(f"- **Раздел**: {section}\n\n")
            continue
        
        # Создаём символы и связи
        for symbol_latex in symbols:
            # Проверяем кеш
            if symbol_latex in symbol_cache:
                symbol_id = symbol_cache[symbol_latex]
            else:
                # Создаём новый символ
                metadata = {
                    'source': 'hyperfrequency_mechanics',
                    'auto_generated': True
                }
                symbol_id = create_symbol_if_not_exists(
                    conn, 
                    symbol_latex,
                    description=f"Автоматически извлечено из формул гиперчастотной механики",
                    metadata=metadata
                )
                symbol_cache[symbol_latex] = symbol_id
                total_symbols_created += 1
            
            # Создаём связь
            link_formula_to_symbol(conn, formula_id, symbol_id)
            total_links_created += 1
    
    print("\n" + "=" * 80)
    print("Результаты:")
    print(f"  Создано уникальных символов: {total_symbols_created}")
    print(f"  Создано связей USES_SYMBOL: {total_links_created}")
    print("=" * 80)
    
    # Записываем лог
    issues.append(f"\n## Статистика\n\n")
    issues.append(f"- Создано уникальных символов: {total_symbols_created}\n")
    issues.append(f"- Создано связей: {total_links_created}\n")
    issues.append(f"- Обработано формул: {len(formulas)}\n")
    
    # Топ-10 самых используемых символов
    print("\nПолучение статистики по символам...")
    stats_query = """
    MATCH (s:Symbol)<-[:USES_SYMBOL]-(f:Formula)
    WHERE s.metadata CONTAINS 'hyperfrequency_mechanics'
    WITH s, count(f) as usage_count
    RETURN s.latex as symbol, s.description as description, usage_count
    ORDER BY usage_count DESC
    LIMIT 20
    """
    stats = conn.execute_query(stats_query)
    
    if stats:
        issues.append(f"\n## Топ-20 самых используемых символов\n\n")
        issues.append("| Символ | Описание | Использований |\n")
        issues.append("|--------|----------|---------------|\n")
        
        print("\nТоп-20 самых используемых символов:")
        for s in stats:
            symbol = s['symbol']
            desc = s['description']
            count = s['usage_count']
            issues.append(f"| `{symbol}` | {desc} | {count} |\n")
            print(f"  {symbol:20s} - {count:4d} использований")
    
    # Сохраняем лог
    with open(log_file, 'w', encoding='utf-8') as f:
        f.writelines(issues)
    
    print(f"\nЛог сохранён в: {log_file}")
    print("\n✅ Готово!")


if __name__ == '__main__':
    main()
