"""
Готовые запросы к графу знаний
"""
from typing import List, Dict, Any
from ..utils.neo4j_connection import Neo4jConnection


class GraphQueries:
    """Класс с готовыми запросами к графу"""
    
    def __init__(self, neo4j_conn: Neo4jConnection):
        self.conn = neo4j_conn
    
    def formulas_in_section(self, section_id: str) -> List[Dict[str, Any]]:
        """Найти все формулы в разделе"""
        query = """
        MATCH (s:Section {id: $section_id})-[:HAS_PARAGRAPH]->(p:Paragraph)-[:CONTAINS_FORMULA]->(f:Formula)
        RETURN f.latex as latex, 
               f.metadata.equation_number as equation_number,
               f.type as type
        ORDER BY f.metadata.equation_number
        """
        return self.conn.execute_query(query, {"section_id": section_id})
    
    def trace_formula_derivation(self, equation_number: str) -> List[Dict[str, Any]]:
        """Трассировка вывода формулы"""
        query = """
        MATCH path = (f1:Formula {metadata: {equation_number: $equation_number}})-[:DERIVED_FROM*]->(f2:Formula)
        RETURN [node in nodes(path) | {
            latex: node.latex,
            equation: node.metadata.equation_number
        }] as derivation_chain
        """
        return self.conn.execute_query(query, {"equation_number": equation_number})
    
    def symbol_usage(self, latex: str) -> List[Dict[str, Any]]:
        """Найти все использования символа"""
        query = """
        MATCH (s:Symbol {latex: $latex})<-[:USES_SYMBOL]-(f:Formula)<-[:CONTAINS_FORMULA]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(sec:Section)
        RETURN sec.title as section_title,
               f.metadata.equation_number as equation_number,
               f.latex as formula
        ORDER BY sec.order
        """
        return self.conn.execute_query(query, {"latex": latex})
    
    def related_concepts(self, concept_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Поиск связанных концепций"""
        query = """
        MATCH (c1:Concept {name: $concept_name})-[r:RELATED_TO]-(c2:Concept)
        RETURN c2.name as concept,
               r.relation_type as relation,
               r.strength as strength
        ORDER BY r.strength DESC
        LIMIT $limit
        """
        return self.conn.execute_query(query, {"concept_name": concept_name, "limit": limit})
    
    def top_cited_literature(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Самые цитируемые источники"""
        query = """
        MATCH (l:Literature)<-[:CITES]-(p:Paragraph)
        WITH l, count(p) as citation_count
        RETURN l.number as number,
               l.author as author,
               l.title as title,
               citation_count
        ORDER BY citation_count DESC
        LIMIT $limit
        """
        return self.conn.execute_query(query, {"limit": limit})
    
    def sections_mentioning_concept(self, concept_name: str) -> List[Dict[str, Any]]:
        """Найти разделы, упоминающие концепцию"""
        query = """
        MATCH (c:Concept {name: $concept_name})<-[:MENTIONS]-(p:Paragraph)<-[:HAS_PARAGRAPH]-(s:Section)
        RETURN DISTINCT s.title as section_title,
               s.file_path as file_path,
               s.number as section_number
        ORDER BY s.order
        """
        return self.conn.execute_query(query, {"concept_name": concept_name})
    
    def illustrations_with_formulas(self) -> List[Dict[str, Any]]:
        """Иллюстрации с формулами в подписи"""
        query = """
        MATCH (i:Illustration)-[:FORMULA_IN_CAPTION]->(f:Formula)
        RETURN i.caption as caption,
               collect(f.latex) as formulas
        ORDER BY i.id
        """
        return self.conn.execute_query(query)
    
    def formula_dependencies(self, formula_id: str) -> Dict[str, Any]:
        """Получить все зависимости формулы (символы, связанные формулы)"""
        query = """
        MATCH (f:Formula {id: $formula_id})
        OPTIONAL MATCH (f)-[:USES_SYMBOL]->(s:Symbol)
        OPTIONAL MATCH (f)-[:DERIVED_FROM]->(df:Formula)
        OPTIONAL MATCH (f)-[:REFERENCES_FORMULA]->(rf:Formula)
        RETURN f.latex as formula,
               collect(DISTINCT s.latex) as symbols,
               collect(DISTINCT df.latex) as derived_from,
               collect(DISTINCT rf.latex) as references
        """
        result = self.conn.execute_query(query, {"formula_id": formula_id})
        return result[0] if result else {}
    
    def chapter_statistics(self) -> List[Dict[str, Any]]:
        """Статистика по главам"""
        query = """
        MATCH (ch:Chapter)
        OPTIONAL MATCH (ch)-[:HAS_SECTION]->(s:Section)
        OPTIONAL MATCH (s)-[:HAS_PARAGRAPH]->(p:Paragraph)
        OPTIONAL MATCH (p)-[:CONTAINS_FORMULA]->(f:Formula)
        WITH ch, count(DISTINCT s) as sections,
             count(DISTINCT p) as paragraphs,
             count(DISTINCT f) as formulas
        RETURN ch.title as chapter,
               ch.order as order,
               sections,
               paragraphs,
               formulas
        ORDER BY ch.order
        """
        return self.conn.execute_query(query)
    
    def search_paragraphs_fulltext(self, search_text: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Полнотекстовый поиск по параграфам"""
        query = """
        CALL db.index.fulltext.queryNodes('paragraph_content', $search_text)
        YIELD node, score
        MATCH (node)<-[:HAS_PARAGRAPH]-(s:Section)
        RETURN node.content as content,
               s.title as section_title,
               s.file_path as file_path,
               score
        ORDER BY score DESC
        LIMIT $limit
        """
        return self.conn.execute_query(query, {"search_text": search_text, "limit": limit})
