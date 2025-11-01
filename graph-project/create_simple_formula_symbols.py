#!/usr/bin/env python3
"""
Создание Symbol узлов для простых формул без математических операторов.
Обрабатывает формулы, которые являются:
- Простыми переменными (N, k, T)
- Переменными с индексами (A_0, N_0, V_{ed})
- Переменными с верхними индексами (10^3, A^п_0)
- Химическими формулами ((H_2O)_3, Al_2O_3)
- Константами и референсами

Эти формулы обычно используются как ссылки на символы, а не как выражения.
"""

import hashlib
from datetime import datetime
from neo4j import GraphDatabase


def generate_symbol_id(latex: str) -> str:
    """Генерирует ID для символа на основе LaTeX."""
    return hashlib.md5(latex.encode('utf-8')).hexdigest()[:12]


def create_symbols_from_simple_formulas(session, batch_size: int = 100):
    """
    Находит все простые формулы без операторов и создаёт для них Symbol узлы.
    """
    print("=" * 80)
    print("Создание Symbol узлов для простых формул без операторов")
    print("=" * 80)
    print()
    
    # Собираем все уникальные простые формулы
    print("Шаг 1: Поиск простых формул...")
    
    query = """
    MATCH (f:Formula)
    WHERE NOT f.latex CONTAINS '='
      AND NOT f.latex CONTAINS '+'
      AND NOT f.latex CONTAINS '*'
      AND NOT f.latex CONTAINS '/'
      AND NOT f.latex CONTAINS '\\\\frac'
      AND NOT f.latex CONTAINS '\\\\cdot'
      AND NOT f.latex CONTAINS '\\\\times'
      AND NOT f.latex CONTAINS '\\\\div'
      AND NOT f.latex CONTAINS '<'
      AND NOT f.latex CONTAINS '>'
      AND NOT f.latex CONTAINS '\\\\leq'
      AND NOT f.latex CONTAINS '\\\\geq'
      AND NOT f.latex CONTAINS '\\\\neq'
      AND NOT f.latex CONTAINS '\\\\approx'
      AND NOT f.latex CONTAINS '\\\\pm'
      AND NOT f.latex CONTAINS '\\\\mp'
      AND NOT f.latex CONTAINS '\\\\sum'
      AND NOT f.latex CONTAINS '\\\\int'
      AND NOT f.latex CONTAINS '\\\\prod'
      AND NOT f.latex CONTAINS '\\\\sqrt'
      AND NOT f.latex CONTAINS '\\\\lim'
      AND NOT f.latex CONTAINS '\\\\partial'
    WITH DISTINCT f.latex as latex, count(*) as usage_count
    WHERE size(latex) > 0 AND size(latex) < 50
    RETURN latex, usage_count
    ORDER BY usage_count DESC, latex
    """
    
    formulas = list(session.run(query))
    print(f"Найдено уникальных простых формул: {len(formulas)}")
    print()
    
    # Статистика
    stats = {
        'total_formulas': len(formulas),
        'symbols_created': 0,
        'symbols_already_exist': 0,
        'symbols_updated': 0,
        'errors': []
    }
    
    # Обрабатываем формулы
    print("Шаг 2: Создание Symbol узлов...")
    
    for i, record in enumerate(formulas, 1):
        latex = record['latex']
        usage_count = record['usage_count']
        
        try:
            # Проверяем, существует ли уже Symbol с таким latex
            check_query = """
            MATCH (s:Symbol {latex: $latex})
            RETURN s.id as id, s.definition as definition
            """
            existing = list(session.run(check_query, latex=latex))
            
            if existing:
                stats['symbols_already_exist'] += 1
                # Если definition пустое, можно обновить
                if not existing[0].get('definition'):
                    # Обновляем только если definition пустое
                    update_query = """
                    MATCH (s:Symbol {latex: $latex})
                    WHERE s.definition IS NULL OR s.definition = ''
                    SET s.symbol = $latex,
                        s.note = 'Автоматически создано из простой формулы',
                        s.context_note = 'Используется ' + toString($usage_count) + ' раз(а) в формулах'
                    RETURN s.id as id
                    """
                    session.run(update_query, latex=latex, usage_count=usage_count)
                    stats['symbols_updated'] += 1
            else:
                # Создаём новый Symbol
                symbol_id = generate_symbol_id(latex)
                
                create_query = """
                MERGE (s:Symbol {id: $symbol_id})
                ON CREATE SET 
                    s.latex = $latex,
                    s.symbol = $latex,
                    s.definition = '',
                    s.note = 'Автоматически создано из простой формулы',
                    s.context_note = 'Используется ' + toString($usage_count) + ' раз(а) в формулах',
                    s.created_at = datetime()
                RETURN s.id as id
                """
                
                result = list(session.run(create_query, 
                    symbol_id=symbol_id,
                    latex=latex,
                    usage_count=usage_count
                ))
                
                if result:
                    stats['symbols_created'] += 1
            
            # Прогресс
            if i % 50 == 0:
                print(f"  Обработано {i}/{len(formulas)} формул... "
                      f"(создано: {stats['symbols_created']}, "
                      f"существует: {stats['symbols_already_exist']}, "
                      f"обновлено: {stats['symbols_updated']})")
        
        except Exception as e:
            error_msg = f"Ошибка при обработке формулы '{latex}': {str(e)}"
            stats['errors'].append(error_msg)
            print(f"  ⚠️  {error_msg}")
    
    return stats


def categorize_formulas(session):
    """
    Категоризирует созданные Symbol по типам.
    """
    print()
    print("Шаг 3: Категоризация символов...")
    
    categories = {
        'simple_variable': "Простая переменная (одна буква)",
        'indexed_variable': "Переменная с индексами",
        'power': "Степень числа",
        'chemical': "Химическая формула",
        'greek': "Греческая буква",
        'special': "Специальный символ",
        'other': "Другое"
    }
    
    results = {}
    
    # Простые переменные
    query = """
    MATCH (s:Symbol)
    WHERE s.note = 'Автоматически создано из простой формулы'
      AND size(s.latex) = 1
      AND s.latex =~ '[a-zA-Z]'
    RETURN count(s) as count
    """
    result = session.run(query).single()
    results['simple_variable'] = result['count'] if result else 0
    
    # Переменные с индексами
    query = """
    MATCH (s:Symbol)
    WHERE s.note = 'Автоматически создано из простой формулы'
      AND (s.latex CONTAINS '_' OR s.latex CONTAINS '^')
      AND NOT s.latex =~ '\\\\d+\\\\^\\\\d+'
      AND NOT s.latex CONTAINS 'H_2O'
      AND NOT s.latex CONTAINS 'O_2'
      AND NOT s.latex CONTAINS 'N_2'
    RETURN count(s) as count
    """
    result = session.run(query).single()
    results['indexed_variable'] = result['count'] if result else 0
    
    # Степени чисел
    query = """
    MATCH (s:Symbol)
    WHERE s.note = 'Автоматически создано из простой формулы'
      AND s.latex =~ '\\\\d+\\\\^\\\\d+'
    RETURN count(s) as count
    """
    result = session.run(query).single()
    results['power'] = result['count'] if result else 0
    
    # Химические формулы
    query = """
    MATCH (s:Symbol)
    WHERE s.note = 'Автоматически создано из простой формулы'
      AND (s.latex CONTAINS 'H_2O' 
           OR s.latex CONTAINS 'O_2' 
           OR s.latex CONTAINS 'N_2'
           OR s.latex CONTAINS 'Al_2O_3'
           OR s.latex CONTAINS 'SO_4'
           OR s.latex =~ '.*[A-Z][a-z]?_\\\\d.*')
    RETURN count(s) as count
    """
    result = session.run(query).single()
    results['chemical'] = result['count'] if result else 0
    
    # Греческие буквы
    query = """
    MATCH (s:Symbol)
    WHERE s.note = 'Автоматически создано из простой формулы'
      AND (s.latex CONTAINS '\\\\alpha'
           OR s.latex CONTAINS '\\\\beta'
           OR s.latex CONTAINS '\\\\gamma'
           OR s.latex CONTAINS '\\\\delta'
           OR s.latex CONTAINS '\\\\epsilon'
           OR s.latex CONTAINS '\\\\theta'
           OR s.latex CONTAINS '\\\\lambda'
           OR s.latex CONTAINS '\\\\mu'
           OR s.latex CONTAINS '\\\\pi'
           OR s.latex CONTAINS '\\\\sigma'
           OR s.latex CONTAINS '\\\\tau'
           OR s.latex CONTAINS '\\\\phi'
           OR s.latex CONTAINS '\\\\omega')
    RETURN count(s) as count
    """
    result = session.run(query).single()
    results['greek'] = result['count'] if result else 0
    
    # Специальные символы
    query = """
    MATCH (s:Symbol)
    WHERE s.note = 'Автоматически создано из простой формулы'
      AND (s.latex CONTAINS '\\\\odot'
           OR s.latex CONTAINS '\\\\oplus'
           OR s.latex CONTAINS '\\\\hbar'
           OR s.latex CONTAINS '\\\\infty'
           OR s.latex CONTAINS '\\\\partial')
    RETURN count(s) as count
    """
    result = session.run(query).single()
    results['special'] = result[0]['count'] if result else 0
    
    return results, categories


def save_report(stats: dict, categories: dict, category_results: dict):
    """Сохраняет отчёт о выполнении."""
    report_file = "simple_formula_symbols_report.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write("# Отчёт: Создание Symbol узлов для простых формул\n\n")
        f.write(f"**Дата**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## Общая статистика\n\n")
        f.write(f"- **Всего найдено простых формул**: {stats['total_formulas']}\n")
        f.write(f"- **Создано новых Symbol**: {stats['symbols_created']}\n")
        f.write(f"- **Symbol уже существовало**: {stats['symbols_already_exist']}\n")
        f.write(f"- **Symbol обновлено**: {stats['symbols_updated']}\n")
        
        if stats['errors']:
            f.write(f"- **Ошибок**: {len(stats['errors'])}\n")
        
        f.write("\n## Категории созданных символов\n\n")
        for cat_key, cat_name in categories.items():
            count = category_results.get(cat_key, 0)
            if count > 0:
                f.write(f"- **{cat_name}**: {count}\n")
        
        if stats['errors']:
            f.write("\n## Ошибки\n\n")
            for error in stats['errors'][:20]:
                f.write(f"- {error}\n")
            if len(stats['errors']) > 20:
                f.write(f"\n*...и ещё {len(stats['errors']) - 20} ошибок*\n")
        
        f.write("\n## Примеры созданных символов\n\n")
        f.write("Символы создаются с пустым `definition`, который можно заполнить вручную.\n\n")
        f.write("Запрос для просмотра всех созданных символов:\n\n")
        f.write("```cypher\n")
        f.write("MATCH (s:Symbol)\n")
        f.write("WHERE s.note = 'Автоматически создано из простой формулы'\n")
        f.write("RETURN s.latex, s.symbol, s.context_note\n")
        f.write("ORDER BY s.latex\n")
        f.write("LIMIT 50\n")
        f.write("```\n")
    
    return report_file


def main():
    """Основная функция."""
    # Загрузка конфигурации из .env
    import os
    from pathlib import Path
    
    # Читаем .env файл
    env_file = Path('.env')
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
    
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.getenv('NEO4J_USERNAME', 'neo4j')
    neo4j_password = os.getenv('NEO4J_PASSWORD', 'password')
    neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')
    
    driver = GraphDatabase.driver(
        neo4j_uri,
        auth=(neo4j_user, neo4j_password),
        database=neo4j_database
    )
    
    try:
        with driver.session() as session:
            # Создаём Symbol для простых формул
            stats = create_symbols_from_simple_formulas(session, batch_size=100)
            
            # Категоризируем
            category_results, categories = categorize_formulas(session)
        
        print()
        print("=" * 80)
        print("Результаты:")
        print(f"  Всего обработано формул: {stats['total_formulas']}")
        print(f"  Создано новых Symbol: {stats['symbols_created']}")
        print(f"  Symbol уже существовало: {stats['symbols_already_exist']}")
        print(f"  Symbol обновлено: {stats['symbols_updated']}")
        if stats['errors']:
            print(f"  Ошибок: {len(stats['errors'])}")
        print()
        print("Категории:")
        for cat_key, cat_name in categories.items():
            count = category_results.get(cat_key, 0)
            if count > 0:
                print(f"  - {cat_name}: {count}")
        print("=" * 80)
        print()
        
        # Сохраняем отчёт
        report_file = save_report(stats, categories, category_results)
        print(f"Отчёт сохранён в: {report_file}")
        print("✅ Готово!")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        driver.close()


if __name__ == "__main__":
    main()
