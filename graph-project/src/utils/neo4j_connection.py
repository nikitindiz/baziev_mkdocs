"""
Утилита для работы с Neo4j графом
"""
from neo4j import GraphDatabase
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Класс для работы с Neo4j базой данных"""
    
    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database
        logger.info(f"Connected to Neo4j at {uri}, database: {database}")
    
    def close(self):
        """Закрыть соединение"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Выполнить Cypher запрос"""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def execute_write(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict:
        """Выполнить запись в базу"""
        with self.driver.session(database=self.database) as session:
            def _write_tx(tx):
                result = tx.run(query, parameters or {})
                summary = result.consume()
                return summary
            
            summary = session.execute_write(_write_tx)
            return {
                "nodes_created": summary.counters.nodes_created,
                "relationships_created": summary.counters.relationships_created,
                "properties_set": summary.counters.properties_set
            }
    
    def create_constraints(self):
        """Создать ограничения уникальности"""
        constraints = [
            "CREATE CONSTRAINT formula_id IF NOT EXISTS FOR (f:Formula) REQUIRE f.id IS UNIQUE",
            "CREATE CONSTRAINT symbol_id IF NOT EXISTS FOR (s:Symbol) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT illustration_id IF NOT EXISTS FOR (i:Illustration) REQUIRE i.id IS UNIQUE",
            "CREATE CONSTRAINT table_id IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT literature_id IF NOT EXISTS FOR (l:Literature) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT concept_id IF NOT EXISTS FOR (c:Concept) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT chapter_id IF NOT EXISTS FOR (ch:Chapter) REQUIRE ch.id IS UNIQUE",
            "CREATE CONSTRAINT book_id IF NOT EXISTS FOR (b:Book) REQUIRE b.id IS UNIQUE",
        ]
        
        for constraint in constraints:
            try:
                self.execute_query(constraint)
                logger.info(f"Created constraint: {constraint}")
            except Exception as e:
                logger.warning(f"Constraint already exists or error: {e}")
    
    def create_indexes(self):
        """Создать индексы для быстрого поиска"""
        indexes = [
            "CREATE FULLTEXT INDEX paragraph_content IF NOT EXISTS FOR (p:Paragraph) ON EACH [p.content]",
            "CREATE FULLTEXT INDEX concept_name IF NOT EXISTS FOR (c:Concept) ON EACH [c.name, c.definition]",
            "CREATE INDEX formula_latex IF NOT EXISTS FOR (f:Formula) ON (f.latex)",
            "CREATE INDEX symbol_latex IF NOT EXISTS FOR (s:Symbol) ON (s.latex)",
            "CREATE INDEX literature_number IF NOT EXISTS FOR (l:Literature) ON (l.number)",
        ]
        
        for index in indexes:
            try:
                self.execute_query(index)
                logger.info(f"Created index: {index}")
            except Exception as e:
                logger.warning(f"Index already exists or error: {e}")
    
    def clear_database(self):
        """Очистить всю базу данных (ОСТОРОЖНО!)"""
        logger.warning("Clearing entire database!")
        self.execute_query("MATCH (n) DETACH DELETE n")
        logger.info("Database cleared")
    
    def get_stats(self) -> Dict[str, int]:
        """Получить статистику по узлам и связям"""
        stats = {}
        
        # Количество узлов по типам
        node_types = ["Book", "Chapter", "Section", "Subsection", "Paragraph", 
                      "Formula", "Symbol", "Illustration", "Table", "Literature", "Concept"]
        
        for node_type in node_types:
            result = self.execute_query(f"MATCH (n:{node_type}) RETURN count(n) as count")
            stats[node_type] = result[0]["count"] if result else 0
        
        # Общее количество связей
        result = self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        stats["Relationships"] = result[0]["count"] if result else 0
        
        return stats
