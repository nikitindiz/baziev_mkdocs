"""
Базовые тесты для графа знаний
"""
import pytest
from pathlib import Path
import sys

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection


@pytest.fixture
def config():
    """Загрузить конфигурацию для тестов"""
    return load_config()


@pytest.fixture
def neo4j_conn(config):
    """Создать подключение к Neo4j"""
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    yield conn
    conn.close()


def test_neo4j_connection(neo4j_conn):
    """Тест подключения к Neo4j"""
    result = neo4j_conn.execute_query("RETURN 1 as num")
    assert result[0]['num'] == 1


def test_get_stats(neo4j_conn):
    """Тест получения статистики"""
    stats = neo4j_conn.get_stats()
    assert isinstance(stats, dict)
    assert 'Relationships' in stats


def test_formula_query(neo4j_conn):
    """Тест запроса формул"""
    query = "MATCH (f:Formula) RETURN count(f) as count"
    result = neo4j_conn.execute_query(query)
    assert isinstance(result[0]['count'], int)


def test_symbol_query(neo4j_conn):
    """Тест запроса символов"""
    query = "MATCH (s:Symbol) RETURN count(s) as count"
    result = neo4j_conn.execute_query(query)
    assert isinstance(result[0]['count'], int)
