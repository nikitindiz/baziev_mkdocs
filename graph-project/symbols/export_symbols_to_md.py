#!/usr/bin/env python3
"""
Скрипт для экспорта всех символов из Neo4j базы в markdown файл.
Генерирует структурированный список символов с их описаниями и использованием.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from neo4j import GraphDatabase
import yaml
from datetime import datetime


def load_config():
    """Загружает конфигурацию из config.yml"""
    config_path = project_root / "config" / "config.yml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def connect_to_neo4j(config):
    """Создает подключение к Neo4j"""
    neo4j_config = config['neo4j']
    driver = GraphDatabase.driver(
        neo4j_config['uri'],
        auth=(neo4j_config['username'], neo4j_config['password'])
    )
    return driver


def fetch_all_symbols(driver, database):
    """Получает все символы из базы данных с дополнительной информацией"""
    query = """
    MATCH (s:Symbol)
    OPTIONAL MATCH (s)-[r]->(entity)
    WITH s, 
         collect(DISTINCT type(r)) as relation_types,
         collect(DISTINCT labels(entity)[0]) as entity_types,
         count(DISTINCT entity) as usage_count,
         properties(s) as props
    RETURN s.id as id,
           coalesce(s.symbol, s.latex, s.name) as symbol,
           s.latex as latex,
           coalesce(s.description, s.desc) as description,
           s.unit as unit,
           s.category as category,
           entity_types,
           usage_count,
           relation_types,
           props
    ORDER BY coalesce(s.symbol, s.latex, s.name)
    """
    
    with driver.session(database=database) as session:
        result = session.run(query)
        return [dict(record) for record in result]


def fetch_statistics(driver, database):
    """Получает статистику по символам"""
    query = """
    MATCH (s:Symbol)
    WITH count(s) as total_symbols,
         count(DISTINCT coalesce(s.category, 'uncategorized')) as categories_count
    MATCH (s:Symbol)
    OPTIONAL MATCH (s)-[]->(entity)
    WITH total_symbols, categories_count, s, count(entity) as usage
    RETURN total_symbols,
           categories_count,
           count(CASE WHEN usage > 0 THEN 1 END) as used_symbols,
           count(CASE WHEN usage = 0 THEN 1 END) as unused_symbols
    """
    
    with driver.session(database=database) as session:
        result = session.run(query)
        record = result.single()
        return dict(record) if record else {}


def generate_markdown(symbols, statistics, output_path):
    """Генерирует markdown файл со списком символов"""
    
    # Группируем символы по категориям
    by_category = {}
    for symbol in symbols:
        category = symbol.get('category') or 'Без категории'
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(symbol)
    
    # Начинаем генерацию markdown
    md_lines = [
        "# Список символов из Neo4j базы",
        "",
        f"*Сгенерировано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
        "## Статистика",
        "",
        f"- **Всего символов:** {statistics.get('total_symbols', 0)}",
        f"- **Используемых символов:** {statistics.get('used_symbols', 0)}",
        f"- **Неиспользуемых символов:** {statistics.get('unused_symbols', 0)}",
        f"- **Категорий:** {statistics.get('categories_count', 0)}",
        "",
        "---",
        "",
    ]
    
    # Добавляем содержание
    md_lines.extend([
        "## Содержание",
        "",
    ])
    
    for category in sorted(by_category.keys()):
        anchor = category.lower().replace(' ', '-').replace('_', '-')
        md_lines.append(f"- [{category}](#{anchor}) ({len(by_category[category])} символов)")
    
    md_lines.extend(["", "---", ""])
    
    # Добавляем символы по категориям
    for category in sorted(by_category.keys()):
        md_lines.extend([
            f"## {category}",
            "",
        ])
        
        category_symbols = sorted(by_category[category], key=lambda x: x.get('symbol') or '')
        
        for sym in category_symbols:
            symbol = sym.get('symbol') or sym.get('latex', '?')
            latex = sym.get('latex', '')
            description = sym.get('description', 'Нет описания')
            unit = sym.get('unit', '')
            usage_count = sym.get('usage_count', 0)
            entity_types = sym.get('entity_types', [])
            relation_types = sym.get('relation_types', [])
            symbol_id = sym.get('id', '')
            props = sym.get('props', {})
            
            # Заголовок символа
            if latex:
                md_lines.append(f"### ${latex}$")
            else:
                md_lines.append(f"### `{symbol}`")
            md_lines.append("")
            
            # Таблица с информацией
            md_lines.extend([
                "| Поле | Значение |",
                "|------|----------|",
            ])
            
            if symbol_id:
                md_lines.append(f"| **ID** | `{symbol_id}` |")
            
            if latex:
                md_lines.append(f"| **LaTeX** | `{latex}` |")
            
            md_lines.append(f"| **Описание** | {description} |")
            
            if unit:
                md_lines.append(f"| **Единица** | {unit} |")
            
            md_lines.append(f"| **Использований** | {usage_count} |")
            
            if relation_types:
                types_str = ", ".join(sorted(set(t for t in relation_types if t)))
                if types_str:
                    md_lines.append(f"| **Типы связей** | {types_str} |")
            
            if entity_types:
                types_str = ", ".join(sorted(set(t for t in entity_types if t)))
                if types_str:
                    md_lines.append(f"| **Связанные сущности** | {types_str} |")
            
            # Дополнительные свойства
            extra_props = {k: v for k, v in props.items() if k not in ['id', 'latex', 'symbol', 'name', 'description', 'desc', 'unit', 'category'] and v is not None}
            if extra_props:
                for key, value in sorted(extra_props.items()):
                    if isinstance(value, str) and len(value) < 100:
                        md_lines.append(f"| **{key}** | {value} |")
            
            md_lines.extend(["", ""])
    
    # Добавляем footer
    md_lines.extend([
        "---",
        "",
        f"*Всего символов: {len(symbols)}*",
        "",
    ])
    
    # Записываем в файл
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    print(f"✓ Markdown файл сохранен: {output_path}")


def main():
    """Основная функция"""
    print("Экспорт символов из Neo4j в Markdown...")
    print("-" * 60)
    
    # Загружаем конфигурацию
    config = load_config()
    print(f"✓ Конфигурация загружена")
    
    # Подключаемся к Neo4j
    driver = connect_to_neo4j(config)
    database = config['neo4j']['database']
    print(f"✓ Подключение к Neo4j установлено (база: {database})")
    
    try:
        # Получаем статистику
        statistics = fetch_statistics(driver, database)
        print(f"✓ Статистика получена: {statistics.get('total_symbols', 0)} символов")
        
        # Получаем все символы
        symbols = fetch_all_symbols(driver, database)
        print(f"✓ Загружено {len(symbols)} символов")
        
        # Генерируем markdown
        output_path = Path(__file__).parent / "symbols_list.md"
        generate_markdown(symbols, statistics, output_path)
        
        print("-" * 60)
        print("✓ Экспорт завершен успешно!")
        
        # Выводим краткую статистику
        if statistics:
            print(f"\nВсего символов: {statistics.get('total_symbols', 0)}")
            print(f"Используемых: {statistics.get('used_symbols', 0)}")
            print(f"Неиспользуемых: {statistics.get('unused_symbols', 0)}")
        
    finally:
        driver.close()
        print("\n✓ Соединение закрыто")


if __name__ == "__main__":
    main()
