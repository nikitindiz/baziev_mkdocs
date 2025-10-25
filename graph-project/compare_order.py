#!/usr/bin/env python3
"""
Сравнение порядка параграфов из Neo4j и исходного файла
"""
import yaml
import re
from pathlib import Path
from src.utils.neo4j_connection import Neo4jConnection


def extract_paragraphs_from_md(file_path):
    """Извлечь параграфы из markdown файла"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Разделить по двойным переводам строки
    blocks = re.split(r'\n\n+', content)
    
    paragraphs = []
    for block in blocks:
        block = block.strip()
        
        # Пропустить заголовки и пустые блоки
        if not block or block.startswith('#') or block.startswith('{{'):
            continue
        
        paragraphs.append(block)
    
    return paragraphs


def compare_paragraphs():
    """Сравнить параграфы из Neo4j и исходного файла"""
    
    # Загрузить конфигурацию
    with open('config/config.yml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Подключиться к Neo4j
    neo4j = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    
    # Получить параграфы из Neo4j
    query = """
    MATCH (ch:Chapter)
    WHERE ch.order = 1
    MATCH (ch)-[:HAS_SECTION]->(s:Section)
    WHERE s.order = 1
    MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
    RETURN s.file_path as file_path,
           p.order as para_order,
           p.content as content
    ORDER BY p.order
    LIMIT 3
    """
    
    neo4j_results = neo4j.execute_query(query)
    neo4j.close()
    
    if not neo4j_results:
        print("❌ Параграфы из Neo4j не найдены!")
        return
    
    # Получить параграфы из исходного файла
    file_path = Path(neo4j_results[0]['file_path'])
    md_paragraphs = extract_paragraphs_from_md(file_path)
    
    print("=" * 100)
    print("СРАВНЕНИЕ ПОРЯДКА ПАРАГРАФОВ")
    print("=" * 100)
    print(f"\nИсходный файл: {file_path}")
    print(f"Параграфов в Neo4j: {len(neo4j_results)}")
    print(f"Параграфов в файле (первые текстовые блоки): {len(md_paragraphs[:3])}")
    
    for i in range(3):
        print(f"\n{'='*100}")
        print(f"ПАРАГРАФ #{i+1}")
        print(f"{'='*100}")
        
        neo4j_para = neo4j_results[i]['content'] if i < len(neo4j_results) else "НЕТ ДАННЫХ"
        md_para = md_paragraphs[i] if i < len(md_paragraphs) else "НЕТ ДАННЫХ"
        
        print(f"\n📊 Neo4j (order={neo4j_results[i]['para_order'] if i < len(neo4j_results) else 'N/A'}):")
        print(f"{neo4j_para[:200]}...")
        
        print(f"\n📄 Markdown (блок #{i+1}):")
        print(f"{md_para[:200]}...")
        
        # Проверка совпадения (первые 100 символов)
        if neo4j_para[:100] == md_para[:100]:
            print(f"\n✅ СОВПАДАЕТ!")
        else:
            print(f"\n⚠️  РАЗЛИЧАЕТСЯ!")
            print(f"\nРазница в начале:")
            print(f"Neo4j:    {neo4j_para[:50]}")
            print(f"Markdown: {md_para[:50]}")
    
    print(f"\n{'='*100}")
    print("ИТОГОВАЯ ПРОВЕРКА")
    print(f"{'='*100}")
    
    all_match = True
    for i in range(min(3, len(neo4j_results), len(md_paragraphs))):
        neo4j_para = neo4j_results[i]['content']
        md_para = md_paragraphs[i]
        if neo4j_para != md_para:
            all_match = False
            break
    
    if all_match:
        print("\n✅ ВСЕ 3 ПАРАГРАФА ИДУТ В ТОМ ЖЕ ПОРЯДКЕ, ЧТО И В ИСХОДНИКЕ!")
    else:
        print("\n⚠️  Обнаружены различия в порядке или содержании параграфов")
    
    print()


if __name__ == '__main__':
    compare_paragraphs()
