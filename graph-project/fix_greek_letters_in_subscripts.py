#!/usr/bin/env python3
"""
Скрипт для исправления греческих букв, обернутых в \\text{} в формулах Neo4j.

Проблема: греческие буквы ошибочно обернуты в \\text{}, например:
- \\text{\\alpha} вместо \\alpha
- \\text{\\lambda} вместо \\lambda

Решение: заменяем все вхождения \\text{\\<greek_letter>} на \\<greek_letter>
"""

import os
import yaml
from neo4j import GraphDatabase

# Загрузка конфигурации
def load_config():
    """Загрузить конфигурацию из config.yml."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Загружаем конфигурацию
config = load_config()
neo4j_config = config['neo4j']

# Конфигурация Neo4j
NEO4J_URI = neo4j_config['uri']
NEO4J_USER = neo4j_config['username']
NEO4J_PASSWORD = neo4j_config['password']

# Список греческих букв для замены
GREEK_LETTERS = [
    'alpha',    # α
    'beta',     # β
    'gamma',    # γ
    'delta',    # δ
    'epsilon',  # ε
    'zeta',     # ζ
    'eta',      # η
    'theta',    # θ
    'iota',     # ι
    'kappa',    # κ
    'lambda',   # λ
    'mu',       # μ
    'nu',       # ν
    'xi',       # ξ
    'omicron',  # ο
    'pi',       # π
    'rho',      # ρ
    'sigma',    # σ
    'tau',      # τ
    'upsilon',  # υ
    'phi',      # φ
    'chi',      # χ
    'psi',      # ψ
    'omega',    # ω
    # Заглавные греческие буквы
    'Gamma',    # Γ
    'Delta',    # Δ
    'Theta',    # Θ
    'Lambda',   # Λ
    'Xi',       # Ξ
    'Pi',       # Π
    'Sigma',    # Σ
    'Upsilon',  # Υ
    'Phi',      # Φ
    'Psi',      # Ψ
    'Omega',    # Ω
]


def get_affected_formulas_count(driver):
    """Подсчитать количество затронутых формул."""
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Formula)
            WHERE f.latex CONTAINS '\\\\text{\\\\'
            RETURN count(f) as count
        """)
        record = result.single()
        return record['count'] if record else 0


def get_sample_formulas(driver, limit=10):
    """Получить примеры формул для проверки."""
    with driver.session() as session:
        result = session.run("""
            MATCH (f:Formula)
            WHERE f.latex CONTAINS '\\\\text{\\\\'
            RETURN f.id, f.latex
            LIMIT $limit
        """, limit=limit)
        return [(record['f.id'], record['f.latex']) for record in result]


def fix_greek_letters_in_formula(latex_string):
    """
    Заменить все вхождения \\text{\\<greek_letter>} на \\<greek_letter>.
    
    Args:
        latex_string: исходная LaTeX строка
        
    Returns:
        исправленная LaTeX строка
    """
    fixed = latex_string
    
    for letter in GREEK_LETTERS:
        # Заменяем \\text{\\letter} на \\letter
        pattern = f'\\text{{\\{letter}}}'
        replacement = f'\\{letter}'
        fixed = fixed.replace(pattern, replacement)
    
    return fixed


def test_fix_function():
    """Тестирование функции исправления."""
    test_cases = [
        (
            r'\eta_{\text{\pi}}(\Delta \varphi) = \Delta \varphi / 2\pi',
            r'\eta_{\pi}(\Delta \varphi) = \Delta \varphi / 2\pi'
        ),
        (
            r'\mu_{\text{\lambda}}',
            r'\mu_{\lambda}'
        ),
        (
            r'n_{\text{\alpha}}',
            r'n_{\alpha}'
        ),
        (
            r'd_{\text{\lambda}}',
            r'd_{\lambda}'
        ),
        (
            r'Z_{\text{\lambda}} = S_{\text{\lambda}} \cdot j_{n}',
            r'Z_{\lambda} = S_{\lambda} \cdot j_{n}'
        ),
        # Должно сохранить легитимное использование \text
        (
            r'1,9876643 \cdot 10^{-27} \quad \text{Кл}',
            r'1,9876643 \cdot 10^{-27} \quad \text{Кл}'
        ),
    ]
    
    print("Тестирование функции исправления...")
    all_passed = True
    
    for i, (input_str, expected) in enumerate(test_cases, 1):
        result = fix_greek_letters_in_formula(input_str)
        passed = result == expected
        status = "✓" if passed else "✗"
        
        print(f"\nТест {i}: {status}")
        print(f"  Вход:    {input_str}")
        print(f"  Ожидал:  {expected}")
        print(f"  Получил: {result}")
        
        if not passed:
            all_passed = False
    
    return all_passed


def update_formulas_in_database(driver, dry_run=True):
    """
    Обновить формулы в базе данных.
    
    Args:
        driver: Neo4j driver
        dry_run: если True, только показать что будет изменено
        
    Returns:
        количество обновленных формул
    """
    with driver.session() as session:
        # Получить все формулы с греческими буквами в \text{}
        result = session.run("""
            MATCH (f:Formula)
            WHERE f.latex CONTAINS '\\\\text{\\\\'
            RETURN f.id as id, f.latex as old_latex
        """)
        
        formulas_to_update = []
        for record in result:
            formula_id = record['id']
            old_latex = record['old_latex']
            new_latex = fix_greek_letters_in_formula(old_latex)
            
            # Проверяем, что действительно что-то изменилось
            if old_latex != new_latex:
                formulas_to_update.append((formula_id, old_latex, new_latex))
        
        print(f"\nНайдено формул для обновления: {len(formulas_to_update)}")
        
        if dry_run:
            print("\n=== DRY RUN MODE - изменения НЕ будут применены ===\n")
            # Показать первые 10 примеров
            for i, (fid, old, new) in enumerate(formulas_to_update[:10], 1):
                print(f"\n{i}. Formula ID: {fid}")
                print(f"   Старая: {old}")
                print(f"   Новая:  {new}")
            
            if len(formulas_to_update) > 10:
                print(f"\n... и еще {len(formulas_to_update) - 10} формул")
            
            return 0
        else:
            print("\n=== ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ ===\n")
            updated_count = 0
            
            for formula_id, old_latex, new_latex in formulas_to_update:
                session.run("""
                    MATCH (f:Formula {id: $id})
                    SET f.latex = $new_latex
                """, id=formula_id, new_latex=new_latex)
                updated_count += 1
                
                if updated_count % 100 == 0:
                    print(f"Обновлено формул: {updated_count}")
            
            print(f"\nВсего обновлено формул: {updated_count}")
            return updated_count


def main():
    """Основная функция."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Исправить греческие буквы в формулах Neo4j'
    )
    parser.add_argument(
        '--apply',
        action='store_true',
        help='Применить изменения (по умолчанию только показать)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Запустить тесты функции исправления'
    )
    
    args = parser.parse_args()
    
    # Запустить тесты, если указан флаг
    if args.test:
        success = test_fix_function()
        return 0 if success else 1
    
    # Подключение к базе данных
    print("Подключение к Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    try:
        # Проверка подключения
        driver.verify_connectivity()
        print("✓ Подключение установлено")
        
        # Получить статистику
        count = get_affected_formulas_count(driver)
        print(f"\nВсего формул с \\text{{\\: {count}")
        
        # Показать примеры
        print("\nПримеры формул (первые 5):")
        samples = get_sample_formulas(driver, limit=5)
        for i, (fid, latex) in enumerate(samples, 1):
            print(f"{i}. [{fid}] {latex[:100]}...")
        
        # Обновить формулы
        dry_run = not args.apply
        updated = update_formulas_in_database(driver, dry_run=dry_run)
        
        if dry_run:
            print("\n" + "="*70)
            print("Для применения изменений запустите скрипт с флагом --apply:")
            print("  python fix_greek_letters_in_subscripts.py --apply")
            print("="*70)
        else:
            print(f"\n✓ Успешно обновлено формул: {updated}")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        driver.close()


if __name__ == '__main__':
    exit(main())
