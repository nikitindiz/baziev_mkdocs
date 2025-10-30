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
    RETURN s.id as id,
           s.latex as latex,
           s.symbol as symbol,
           s.definition as definition,
           s.description as description,
           s.unit as unit,
           s.source as source,
           s.latex_corrected as latex_corrected,
           s.latex_note as latex_note,
           s.latex_context as latex_context,
           s.context_note as context_note,
           s.note as note,
           s.confidence as confidence,
           s.auto_generated as auto_generated,
           s.created_at as created_at
    ORDER BY s.latex
    """
    
    results = neo4j_conn.execute_query(query)
    return results

def escape_markdown(text):
    """Экранирование специальных символов для Markdown таблицы"""
    if text is None:
        return ""
    text = str(text)
    # Заменяем символы, которые могут сломать таблицу
    text = text.replace('|', '\\|')
    text = text.replace('\n', ' ')
    text = text.replace('\r', ' ')
    return text

def generate_markdown(symbols, output_file="symbols_list.md"):
    """Генерация Markdown файла со списком символов в виде таблицы"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # Заголовок
        f.write("# Список символов из базы данных\n\n")
        f.write(f"Всего символов: **{len(symbols)}**\n\n")
        f.write("---\n\n")
        
        # Заголовок таблицы
        headers = [
            "ID",
            "LaTeX",
            "Symbol",
            "Definition",
            "Description",
            "Unit",
            "Source",
            "LaTeX Corrected",
            "LaTeX Note",
            "LaTeX Context",
            "Context Note",
            "Note",
            "Confidence",
            "Auto Generated",
            "Created At"
        ]
        
        # Создаём таблицу
        f.write("| " + " | ".join(headers) + " |\n")
        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
        
        # Данные таблицы
        for symbol in symbols:
            row = [
                escape_markdown(symbol.get('id', '')),
                f"${escape_markdown(symbol.get('latex', ''))}$" if symbol.get('latex') else '',
                escape_markdown(symbol.get('symbol', '')),
                escape_markdown(symbol.get('definition', '')),
                escape_markdown(symbol.get('description', '')),
                escape_markdown(symbol.get('unit', '')),
                escape_markdown(symbol.get('source', '')),
                f"${escape_markdown(symbol.get('latex_corrected', ''))}$" if symbol.get('latex_corrected') else '',
                escape_markdown(symbol.get('latex_note', '')),
                escape_markdown(symbol.get('latex_context', '')),
                escape_markdown(symbol.get('context_note', '')),
                escape_markdown(symbol.get('note', '')),
                escape_markdown(symbol.get('confidence', '')),
                escape_markdown(symbol.get('auto_generated', '')),
                escape_markdown(symbol.get('created_at', ''))
            ]
            
            f.write("| " + " | ".join(row) + " |\n")
    
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
