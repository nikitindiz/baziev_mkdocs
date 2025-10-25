"""
Визуализация графа с использованием различных библиотек
"""
import logging
from pathlib import Path
from typing import List, Dict, Optional
from ..utils.neo4j_connection import Neo4jConnection

logger = logging.getLogger(__name__)


class GraphVisualizer:
    """Визуализация графа знаний"""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        self.conn = neo4j_conn
    
    def visualize_chapter_structure(self, chapter_id: str, output_path: Path):
        """Визуализировать структуру главы в виде HTML"""
        try:
            import networkx as nx
            from pyvis.network import Network
        except ImportError:
            logger.error("Требуется установить networkx и pyvis: pip install networkx pyvis")
            return
        
        logger.info(f"Visualizing chapter structure: {chapter_id}")
        
        # Получить данные главы
        query = """
        MATCH (ch:Chapter {id: $chapter_id})-[:HAS_SECTION]->(s:Section)
        OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
        OPTIONAL MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
        RETURN ch, s, collect(DISTINCT p) as paragraphs, collect(DISTINCT f) as formulas
        """
        
        results = self.conn.execute_query(query, {"chapter_id": chapter_id})
        
        # Создать граф
        net = Network(height="750px", width="100%", bgcolor="#222222", font_color="white")
        net.barnes_hut()
        
        for result in results:
            ch = result['ch']
            s = result['s']
            
            # Добавить узлы
            net.add_node(ch['id'], label=ch['title'], color='#ff6b6b', size=30)
            net.add_node(s['id'], label=s['title'], color='#4ecdc4', size=20)
            net.add_edge(ch['id'], s['id'])
            
            # Добавить параграфы
            for p in result['paragraphs']:
                if p:
                    label = p['content'][:30] + '...' if len(p['content']) > 30 else p['content']
                    net.add_node(p['id'], label=label, color='#95e1d3', size=10)
                    net.add_edge(s['id'], p['id'])
            
            # Добавить формулы
            for f in result['formulas']:
                if f:
                    label = f.get('latex', 'Formula')[:20] + '...'
                    net.add_node(f['id'], label=label, color='#f38181', size=8, shape='box')
                    # Связать с параграфами через которые они входят
        
        # Сохранить
        net.save_graph(str(output_path))
        logger.info(f"Visualization saved to {output_path}")
    
    def visualize_formula_dependencies(self, formula_id: str, output_path: Path, depth: int = 2):
        """Визуализировать зависимости формулы"""
        try:
            from pyvis.network import Network
        except ImportError:
            logger.error("Требуется установить pyvis: pip install pyvis")
            return
        
        logger.info(f"Visualizing formula dependencies: {formula_id}")
        
        # Получить формулу и её связи
        query = """
        MATCH (f:Formula {id: $formula_id})
        OPTIONAL MATCH path = (f)-[:USES_SYMBOL*1..{depth}]-(s:Symbol)
        OPTIONAL MATCH (f)-[:DERIVED_FROM]-(df:Formula)
        RETURN f, collect(DISTINCT s) as symbols, collect(DISTINCT df) as derived
        """.replace("{depth}", str(depth))
        
        result = self.conn.execute_query(query, {"formula_id": formula_id})
        
        if not result:
            logger.warning(f"Formula {formula_id} not found")
            return
        
        net = Network(height="600px", width="100%", bgcolor="#ffffff", font_color="black")
        
        f = result[0]['f']
        net.add_node(f['id'], 
                    label=f.get('latex', 'Formula')[:50], 
                    color='#e74c3c', 
                    size=30,
                    title=f.get('latex', ''))
        
        # Добавить символы
        for s in result[0]['symbols']:
            if s:
                net.add_node(s['id'], 
                           label=s['latex'], 
                           color='#3498db', 
                           size=15,
                           shape='box',
                           title=s.get('description', ''))
                net.add_edge(f['id'], s['id'], label='USES_SYMBOL')
        
        # Добавить связанные формулы
        for df in result[0]['derived']:
            if df:
                net.add_node(df['id'], 
                           label=df.get('latex', 'Formula')[:30], 
                           color='#f39c12', 
                           size=20)
                net.add_edge(f['id'], df['id'], label='DERIVED_FROM')
        
        net.save_graph(str(output_path))
        logger.info(f"Visualization saved to {output_path}")
    
    def generate_concept_map(self, output_path: Path, limit: int = 100):
        """Создать карту концепций"""
        try:
            from pyvis.network import Network
        except ImportError:
            logger.error("Требуется установить pyvis: pip install pyvis")
            return
        
        logger.info("Generating concept map...")
        
        query = """
        MATCH (c:Concept)
        OPTIONAL MATCH (c)-[r:RELATED_TO]-(c2:Concept)
        WITH c, collect({concept: c2, relation: r}) as related
        RETURN c, related
        LIMIT $limit
        """
        
        concepts = self.conn.execute_query(query, {"limit": limit})
        
        net = Network(height="800px", width="100%", bgcolor="#f5f5f5")
        net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=200)
        
        for concept in concepts:
            c = concept['c']
            net.add_node(c['id'], 
                        label=c['name'], 
                        title=c.get('definition', ''),
                        size=20)
            
            for rel in concept['related']:
                if rel['concept']:
                    c2 = rel['concept']
                    if not net.get_node(c2['id']):
                        net.add_node(c2['id'], label=c2['name'], size=15)
                    
                    if rel['relation']:
                        net.add_edge(c['id'], c2['id'], 
                                   label=rel['relation'].get('relation_type', ''))
        
        net.save_graph(str(output_path))
        logger.info(f"Concept map saved to {output_path}")
