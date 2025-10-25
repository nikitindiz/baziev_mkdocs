#!/usr/bin/env python3
"""
Скрипт для добавления недостающих связей CONTAINS_FORMULA между параграфами и формулами
"""
import re
import json
import logging
import sys
from pathlib import Path
from tqdm import tqdm

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_formula_links():
    """Добавить недостающие связи между параграфами и формулами"""
    
    # Загрузить конфигурацию
    config = load_config()
    
    # Подключиться к Neo4j
    conn = Neo4jConnection(
        uri=config["neo4j"]["uri"],
        user=config["neo4j"]["username"],
        password=config["neo4j"]["password"],
        database=config["neo4j"]["database"]
    )
    
    logger.info("Подключение к Neo4j установлено")
    
    # Регулярное выражение для поиска формул
    formula_pattern = re.compile(r'\{\{formula:([a-f0-9]{12})(?::\([^)]+\))?\}\}')
    
    # Получить все параграфы с ссылками на формулы, но без связей
    query = """
    MATCH (p:Paragraph)
    WHERE p.content CONTAINS 'formula:'
    AND NOT (p)-[:CONTAINS_FORMULA]->(:Formula)
    RETURN p.id as id, p.content as content
    """
    
    paragraphs = conn.execute_query(query)
    logger.info(f"Найдено {len(paragraphs)} параграфов без связей с формулами")
    
    if not paragraphs:
        logger.info("Все параграфы уже связаны с формулами!")
        conn.close()
        return
    
    # Счетчики
    total_links_created = 0
    total_formulas_not_found = 0
    formulas_not_found = set()
    
    # Обработать каждый параграф
    for para in tqdm(paragraphs, desc="Обработка параграфов"):
        para_id = para['id']
        content = para['content']
        
        # Найти все ссылки на формулы в контенте
        matches = formula_pattern.finditer(content)
        
        for match in matches:
            formula_id = match.group(1)
            position = match.start()
            
            # Проверить, существует ли формула
            check_query = """
            MATCH (f:Formula {id: $formula_id})
            RETURN count(f) as count
            """
            result = conn.execute_query(check_query, {"formula_id": formula_id})
            
            if result and result[0]['count'] > 0:
                # Создать связь
                link_query = """
                MATCH (p:Paragraph {id: $para_id})
                MATCH (f:Formula {id: $formula_id})
                MERGE (p)-[r:CONTAINS_FORMULA]->(f)
                SET r.position = $position
                """
                
                conn.execute_query(link_query, {
                    "para_id": para_id,
                    "formula_id": formula_id,
                    "position": position
                })
                
                total_links_created += 1
            else:
                total_formulas_not_found += 1
                formulas_not_found.add(formula_id)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"Создано связей: {total_links_created}")
    logger.info(f"Формул не найдено: {total_formulas_not_found}")
    
    if formulas_not_found:
        logger.warning(f"\nНе найдены следующие формулы:")
        for formula_id in sorted(formulas_not_found):
            logger.warning(f"  - {formula_id}")
    
    # Проверить результат
    verify_query = """
    MATCH (p:Paragraph)
    WHERE p.content CONTAINS 'formula:'
    AND NOT (p)-[:CONTAINS_FORMULA]->(:Formula)
    RETURN count(*) as remaining
    """
    
    result = conn.execute_query(verify_query)
    remaining = result[0]['remaining'] if result else 0
    
    logger.info(f"\nОсталось параграфов без связей: {remaining}")
    
    # Статистика
    stats_query = """
    MATCH (p:Paragraph)-[r:CONTAINS_FORMULA]->(f:Formula)
    RETURN count(DISTINCT p) as paragraphs_with_links,
           count(r) as total_links
    """
    
    stats = conn.execute_query(stats_query)
    if stats:
        logger.info(f"Параграфов со связями: {stats[0]['paragraphs_with_links']}")
        logger.info(f"Всего связей CONTAINS_FORMULA: {stats[0]['total_links']}")
    
    conn.close()
    logger.info("Готово!")


if __name__ == "__main__":
    fix_formula_links()
