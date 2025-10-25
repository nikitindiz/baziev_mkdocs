"""
Утилиты для экспорта графа в различные форматы
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any
from ..utils.neo4j_connection import Neo4jConnection

logger = logging.getLogger(__name__)


class GraphExporter:
    """Экспорт графа в различные форматы"""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        self.conn = neo4j_conn
    
    def export_to_json(self, output_path: Path):
        """Экспорт графа в JSON"""
        logger.info(f"Exporting graph to JSON: {output_path}")
        
        # Получить все узлы
        nodes_query = """
        MATCH (n)
        RETURN labels(n) as labels, properties(n) as properties, id(n) as neo4j_id
        """
        nodes = self.conn.execute_query(nodes_query)
        
        # Получить все связи
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN id(a) as source, id(b) as target, type(r) as type, properties(r) as properties
        """
        relationships = self.conn.execute_query(rels_query)
        
        graph_data = {
            "nodes": nodes,
            "relationships": relationships
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(graph_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported {len(nodes)} nodes and {len(relationships)} relationships")
    
    def export_to_graphml(self, output_path: Path):
        """Экспорт графа в GraphML формат"""
        logger.info(f"Exporting graph to GraphML: {output_path}")
        
        # GraphML заголовок
        graphml = ['<?xml version="1.0" encoding="UTF-8"?>']
        graphml.append('<graphml xmlns="http://graphml.graphdrawing.org/xmlns">')
        graphml.append('  <graph id="G" edgedefault="directed">')
        
        # Узлы
        nodes_query = "MATCH (n) RETURN id(n) as id, labels(n) as labels, properties(n) as props"
        nodes = self.conn.execute_query(nodes_query)
        
        for node in nodes:
            labels = ','.join(node['labels'])
            graphml.append(f'    <node id="n{node["id"]}" labels="{labels}"/>')
        
        # Связи
        rels_query = """
        MATCH (a)-[r]->(b)
        RETURN id(a) as source, id(b) as target, type(r) as type
        """
        rels = self.conn.execute_query(rels_query)
        
        for rel in rels:
            graphml.append(f'    <edge source="n{rel["source"]}" target="n{rel["target"]}" label="{rel["type"]}"/>')
        
        graphml.append('  </graph>')
        graphml.append('</graphml>')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(graphml))
        
        logger.info(f"Exported to GraphML")
    
    def export_glossary(self, output_path: Path):
        """Экспорт глоссария символов в markdown"""
        logger.info(f"Exporting glossary to: {output_path}")
        
        query = """
        MATCH (s:Symbol)
        OPTIONAL MATCH (s)<-[:USES_SYMBOL]-(f:Formula)
        WITH s, count(f) as usage_count
        RETURN s.latex as latex, 
               s.description as description, 
               usage_count
        ORDER BY s.latex
        """
        symbols = self.conn.execute_query(query)
        
        lines = ['# Глоссарий символов\n']
        lines.append('| Символ | Описание | Использований |\n')
        lines.append('|--------|----------|---------------|\n')
        
        for symbol in symbols:
            latex = symbol['latex'].replace('|', '\\|')
            desc = symbol['description'].replace('|', '\\|')
            count = symbol['usage_count']
            lines.append(f'| ${latex}$ | {desc} | {count} |\n')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"Exported {len(symbols)} symbols to glossary")
    
    def export_formula_index(self, output_path: Path):
        """Экспорт указателя формул в markdown"""
        logger.info(f"Exporting formula index to: {output_path}")
        
        query = """
        MATCH (f:Formula)
        WHERE f.metadata.equation_number IS NOT NULL
        OPTIONAL MATCH (f)<-[:CONTAINS_FORMULA]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(s:Section)
        WITH f, collect(DISTINCT s.title) as sections
        RETURN f.metadata.equation_number as number,
               f.latex as latex,
               sections
        ORDER BY f.metadata.equation_number
        """
        formulas = self.conn.execute_query(query)
        
        lines = ['# Указатель формул\n']
        
        for formula in formulas:
            number = formula['number']
            latex = formula['latex']
            sections = ', '.join(formula['sections']) if formula['sections'] else 'Не указано'
            
            lines.append(f'\n## {number}\n\n')
            lines.append(f'$$\n{latex}\n$$\n\n')
            lines.append(f'**Разделы:** {sections}\n')
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"Exported {len(formulas)} formulas to index")
