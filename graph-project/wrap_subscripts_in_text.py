#!/usr/bin/env python3
"""
Скрипт для обёртывания многосимвольных подстрочных индексов в \\text{}

Обрабатывает индексы типа:
- _{g0} -> _{\\text{g0}}
- _{\\lambda 0i} -> _{\\text{\\lambda 0i}}
- _{H_2O} -> НЕ ТРОГАЕТ (содержит вложенные индексы)

Не обрабатывает:
- Уже обёрнутые в \\text{} или \\mathrm{}
- Одиночные символы (_{0}, _{i})
- Содержащие кириллицу
- Содержащие вложенные _ (сложные формулы)
"""

import re
import sys
from neo4j import GraphDatabase
from typing import List, Tuple, Dict
import os
import yaml

# Загружаем конфигурацию
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# Настройки подключения
NEO4J_URI = config['neo4j']['uri']
NEO4J_USER = config['neo4j']['username']
NEO4J_PASSWORD = config['neo4j']['password']

# Кириллические символы для проверки
CYRILLIC_CHARS = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ')


def has_cyrillic(text: str) -> bool:
    """Проверяет наличие кириллицы в тексте"""
    return any(char in CYRILLIC_CHARS for char in text)


def has_nested_subscripts(text: str) -> bool:
    """Проверяет наличие вложенных подстрочных индексов"""
    # Ищем _ внутри содержимого индекса (после первого _)
    return '_' in text


def should_wrap_subscript(subscript: str) -> bool:
    """
    Определяет, нужно ли обернуть индекс в \\text{}
    
    Условия для обёртывания:
    - Длина > 1
    - Не начинается с \\text{ или \\mathrm{
    - Не содержит кириллицу
    - Не содержит вложенных индексов
    """
    if len(subscript) <= 1:
        return False
    
    if subscript.startswith('\\text{') or subscript.startswith('\\mathrm{'):
        return False
    
    if has_cyrillic(subscript):
        return False
    
    if has_nested_subscripts(subscript):
        return False
    
    return True


def wrap_subscripts_in_latex(latex: str) -> Tuple[str, List[str]]:
    """
    Обрабатывает LaTeX формулу и оборачивает подходящие индексы в \\text{}
    
    Returns:
        Tuple[новая_формула, список_изменений]
    """
    if not latex or '_{' not in latex:
        return latex, []
    
    changes = []
    result = latex
    
    # Паттерн для поиска подстрочных индексов в фигурных скобках
    # Ищем _{ ... } и извлекаем содержимое
    pattern = r'_\{([^}]+)\}'
    
    def replace_subscript(match):
        full_match = match.group(0)  # _{ ... }
        subscript = match.group(1)   # содержимое без _{ и }
        
        if should_wrap_subscript(subscript):
            new_subscript = f'_{{\\text{{{subscript}}}}}'
            changes.append(f'{full_match} -> {new_subscript}')
            return new_subscript
        else:
            return full_match
    
    result = re.sub(pattern, replace_subscript, result)
    
    return result, changes


def process_formulas(driver, dry_run: bool = True) -> Dict:
    """
    Обрабатывает все формулы в базе данных
    
    Args:
        driver: Neo4j driver
        dry_run: если True, не применяет изменения
    
    Returns:
        Dict со статистикой
    """
    stats = {
        'total_formulas': 0,
        'formulas_with_subscripts': 0,
        'formulas_modified': 0,
        'total_changes': 0,
        'examples': []
    }
    
    with driver.session() as session:
        # Получаем все формулы с подстрочными индексами
        result = session.run("""
            MATCH (f:Formula)
            WHERE f.latex IS NOT NULL AND f.latex CONTAINS '_{'
            RETURN f.id as id, f.latex as latex
            ORDER BY f.id
        """)
        
        formulas = list(result)
        stats['total_formulas'] = len(formulas)
        
        for record in formulas:
            formula_id = record['id']
            original_latex = record['latex']
            
            # Проверяем наличие индексов
            if '_{' in original_latex:
                stats['formulas_with_subscripts'] += 1
                
                # Обрабатываем формулу
                new_latex, changes = wrap_subscripts_in_latex(original_latex)
                
                if changes:
                    stats['formulas_modified'] += 1
                    stats['total_changes'] += len(changes)
                    
                    # Сохраняем примеры (первые 20)
                    if len(stats['examples']) < 20:
                        stats['examples'].append({
                            'id': formula_id,
                            'original': original_latex,
                            'new': new_latex,
                            'changes': changes
                        })
                    
                    # Применяем изменения, если не dry-run
                    if not dry_run:
                        session.run("""
                            MATCH (f:Formula {id: $id})
                            SET f.latex_orig = CASE WHEN f.latex_orig IS NULL THEN f.latex ELSE f.latex_orig END,
                                f.latex = $new_latex
                        """, id=formula_id, new_latex=new_latex)
    
    return stats


def print_statistics(stats: Dict, dry_run: bool):
    """Выводит статистику обработки"""
    print("\n" + "="*80)
    print(f"{'DRY RUN MODE' if dry_run else 'APPLYING CHANGES'}")
    print("="*80)
    print(f"\nВсего формул в базе: {stats['total_formulas']}")
    print(f"Формул с подстрочными индексами _{{}}: {stats['formulas_with_subscripts']}")
    print(f"Формул будет изменено: {stats['formulas_modified']}")
    print(f"Всего изменений индексов: {stats['total_changes']}")
    
    if stats['examples']:
        print(f"\n{'='*80}")
        print(f"ПРИМЕРЫ ИЗМЕНЕНИЙ (первые {len(stats['examples'])}):")
        print("="*80)
        
        for i, example in enumerate(stats['examples'], 1):
            print(f"\n{i}. ID: {example['id']}")
            print(f"   БЫЛО:  {example['original']}")
            print(f"   СТАЛО: {example['new']}")
            print(f"   Изменения:")
            for change in example['changes']:
                print(f"     - {change}")


def main():
    """Главная функция"""
    # Проверяем аргументы командной строки
    dry_run = True
    if len(sys.argv) > 1:
        if sys.argv[1] == '--apply':
            dry_run = False
            print("\n⚠️  РЕЖИМ ПРИМЕНЕНИЯ ИЗМЕНЕНИЙ!")
            response = input("Вы уверены? Введите 'yes' для продолжения: ")
            if response.lower() != 'yes':
                print("Отменено.")
                return
        elif sys.argv[1] in ['--help', '-h']:
            print("Использование:")
            print("  python wrap_subscripts_in_text.py          # dry-run режим (по умолчанию)")
            print("  python wrap_subscripts_in_text.py --apply  # применить изменения")
            print("  python wrap_subscripts_in_text.py --help   # показать помощь")
            return
    else:
        print("\n✓ Режим DRY-RUN (изменения не будут применены)")
        print("  Для применения изменений используйте: --apply\n")
    
    # Проверяем настройки подключения
    if not all([NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD]):
        print("❌ Ошибка: не настроены переменные окружения для Neo4j")
        print("   Проверьте NEO4J_URI_2, NEO4J_USER_2, NEO4J_PASSWORD_2")
        return
    
    # Подключаемся к базе данных
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        print(f"✓ Подключено к Neo4j: {NEO4J_URI}")
        
        # Обрабатываем формулы
        stats = process_formulas(driver, dry_run)
        
        # Выводим статистику
        print_statistics(stats, dry_run)
        
        if dry_run:
            print("\n" + "="*80)
            print("Это был DRY-RUN. Для применения изменений используйте:")
            print("  python wrap_subscripts_in_text.py --apply")
            print("="*80)
        else:
            print("\n" + "="*80)
            print("✓ Изменения успешно применены к базе данных!")
            print("="*80)
        
        driver.close()
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
