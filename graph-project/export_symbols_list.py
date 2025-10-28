#!/usr/bin/env python3
"""
Скрипт для экспорта всех символов из Neo4j в Markdown формат.
Формат: * $latex$ - definition | id |
"""

import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection

def connect_to_neo4j():
    """Подключение к Neo4j"""
    config = load_config()
    
    neo4j_conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    return neo4j_conn

def get_all_symbols(neo4j_conn):
    """Получить все символы из базы данных"""
    query = """
    MATCH (s:Symbol)
    RETURN s.latex as latex, s.definition as definition, s.id as id
    ORDER BY s.latex
    """
    
    results = neo4j_conn.execute_query(query)
    return results

def escape_latex(latex_str):
    """Экранирование LaTeX для Markdown"""
    if not latex_str:
        return ""
    # В markdown между $ не нужно дополнительное экранирование
    return latex_str

def generate_markdown(symbols, output_file="symbols_list.md"):
    """Генерация Markdown файла со списком символов"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Заголовок
        f.write("# Список символов из базы данных\n\n")
        f.write(f"Всего символов: **{len(symbols)}**\n\n")
        f.write("---\n\n")
        
        # Список символов
        for symbol in symbols:
            latex = escape_latex(symbol.get('latex', ''))
            definition = symbol.get('definition', 'нет определения')
            symbol_id = symbol.get('id', 'нет id')
            
            # Формат: * $latex$ - definition | id |
            line = f"* ${latex}$ - {definition} | {symbol_id} |\n"
            f.write(line)
    
    print(f"✅ Файл {output_file} успешно создан!")
    print(f"📊 Экспортировано символов: {len(symbols)}")

def main():
    """Основная функция"""
    print("🔄 Подключение к Neo4j...")
    neo4j_conn = connect_to_neo4j()
    
    try:
        print("📥 Загрузка символов из базы данных...")
        symbols = get_all_symbols(neo4j_conn)
        
        print("📝 Генерация Markdown файла...")
        generate_markdown(symbols)
        
    finally:
        neo4j_conn.close()
        print("✅ Подключение к Neo4j закрыто")

if __name__ == "__main__":
    main()
