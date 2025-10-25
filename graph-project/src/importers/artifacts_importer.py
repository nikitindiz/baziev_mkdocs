"""
Импортер семантических артефактов (Formula, Symbol, Illustration, Table, Literature)
"""
import json
import logging
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm
from ..utils.neo4j_connection import Neo4jConnection
from ..models.nodes import Formula, Symbol, Illustration, Table, Literature

logger = logging.getLogger(__name__)


class ArtifactsImporter:
    """Импортер семантических артефактов"""
    
    def __init__(self, neo4j_conn: Neo4jConnection, config: Dict):
        self.conn = neo4j_conn
        self.config = config
        self.batch_size = config["import"]["batch_size"]
    
    def import_formulas(self):
        """Импортировать формулы из JSON файлов"""
        formulas_path = Path(self.config["paths"]["formulas"])
        formula_files = list(formulas_path.glob("formula_*.json"))
        
        logger.info(f"Importing {len(formula_files)} formulas...")
        
        for i in tqdm(range(0, len(formula_files), self.batch_size)):
            batch = formula_files[i:i + self.batch_size]
            self._import_formula_batch(batch)
        
        logger.info(f"Imported {len(formula_files)} formulas")
    
    def _import_formula_batch(self, files: List[Path]):
        """Импортировать пакет формул"""
        formulas = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертируем вложенные объекты в JSON строки
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        data['metadata'] = json.dumps(data['metadata'])
                    if 'source' in data and isinstance(data['source'], dict):
                        data['source'] = json.dumps(data['source'])
                    formulas.append(data)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        query = """
        UNWIND $formulas AS formula
        MERGE (f:Formula {id: formula.id})
        SET f.type = formula.type,
            f.latex = formula.latex,
            f.metadata = formula.metadata,
            f.source = formula.source,
            f.symbols = formula.symbols,
            f.wrapper_html = formula.wrapper_html
        """
        
        self.conn.execute_query(query, {"formulas": formulas})
    
    def import_symbols(self):
        """Импортировать символы из JSON файлов"""
        symbols_path = Path(self.config["paths"]["symbols"])
        symbol_files = list(symbols_path.glob("symbol_*.json"))
        
        logger.info(f"Importing {len(symbol_files)} symbols...")
        
        for i in tqdm(range(0, len(symbol_files), self.batch_size)):
            batch = symbol_files[i:i + self.batch_size]
            self._import_symbol_batch(batch)
        
        logger.info(f"Imported {len(symbol_files)} symbols")
    
    def _import_symbol_batch(self, files: List[Path]):
        """Импортировать пакет символов"""
        symbols = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертируем вложенные объекты в JSON строки
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        data['metadata'] = json.dumps(data['metadata'])
                    symbols.append(data)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        query = """
        UNWIND $symbols AS symbol
        MERGE (s:Symbol {id: symbol.id})
        SET s.latex = symbol.latex,
            s.description = symbol.description,
            s.metadata = symbol.metadata
        """
        
        self.conn.execute_query(query, {"symbols": symbols})
    
    def import_illustrations(self):
        """Импортировать иллюстрации из JSON файлов"""
        illustrations_path = Path(self.config["paths"]["illustrations"])
        illustration_files = list(illustrations_path.glob("illustration_*.json"))
        
        logger.info(f"Importing {len(illustration_files)} illustrations...")
        
        for i in tqdm(range(0, len(illustration_files), self.batch_size)):
            batch = illustration_files[i:i + self.batch_size]
            self._import_illustration_batch(batch)
        
        logger.info(f"Imported {len(illustration_files)} illustrations")
    
    def _import_illustration_batch(self, files: List[Path]):
        """Импортировать пакет иллюстраций"""
        illustrations = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертируем вложенные объекты в JSON строки
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        data['metadata'] = json.dumps(data['metadata'])
                    if 'source' in data and isinstance(data['source'], dict):
                        data['source'] = json.dumps(data['source'])
                    illustrations.append(data)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        query = """
        UNWIND $illustrations AS ill
        MERGE (i:Illustration {id: ill.id})
        SET i.type = ill.type,
            i.svg_content = ill.svg_content,
            i.caption = ill.caption,
            i.metadata = ill.metadata,
            i.source = ill.source,
            i.wrapper_html = ill.wrapper_html
        """
        
        self.conn.execute_query(query, {"illustrations": illustrations})
    
    def import_tables(self):
        """Импортировать таблицы из JSON файлов"""
        tables_path = Path(self.config["paths"]["tables"])
        table_files = list(tables_path.glob("table_*.json"))
        
        logger.info(f"Importing {len(table_files)} tables...")
        
        for i in tqdm(range(0, len(table_files), self.batch_size)):
            batch = table_files[i:i + self.batch_size]
            self._import_table_batch(batch)
        
        logger.info(f"Imported {len(table_files)} tables")
    
    def _import_table_batch(self, files: List[Path]):
        """Импортировать пакет таблиц"""
        tables = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертируем вложенные объекты в JSON строки
                    if 'content' in data and isinstance(data['content'], dict):
                        data['content'] = json.dumps(data['content'])
                    if 'metadata' in data and isinstance(data['metadata'], dict):
                        data['metadata'] = json.dumps(data['metadata'])
                    if 'source' in data and isinstance(data['source'], dict):
                        data['source'] = json.dumps(data['source'])
                    if 'html_attributes' in data and isinstance(data['html_attributes'], dict):
                        data['html_attributes'] = json.dumps(data['html_attributes'])
                    tables.append(data)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        query = """
        UNWIND $tables AS tbl
        MERGE (t:Table {id: tbl.id})
        SET t.type = tbl.type,
            t.content = tbl.content,
            t.metadata = tbl.metadata,
            t.source = tbl.source,
            t.html_attributes = tbl.html_attributes
        """
        
        self.conn.execute_query(query, {"tables": tables})
    
    def import_literature(self):
        """Импортировать литературу из JSON файлов"""
        literature_path = Path(self.config["paths"]["literature"])
        literature_files = list(literature_path.glob("literature_*.json"))
        
        logger.info(f"Importing {len(literature_files)} literature entries...")
        
        for i in tqdm(range(0, len(literature_files), self.batch_size)):
            batch = literature_files[i:i + self.batch_size]
            self._import_literature_batch(batch)
        
        logger.info(f"Imported {len(literature_files)} literature entries")
    
    def _import_literature_batch(self, files: List[Path]):
        """Импортировать пакет литературы"""
        literature = []
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертируем вложенные объекты в JSON строки
                    if 'source' in data and isinstance(data['source'], dict):
                        data['source'] = json.dumps(data['source'])
                    literature.append(data)
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")
        
        query = """
        UNWIND $literature AS lit
        MERGE (l:Literature {id: lit.id})
        SET l.number = lit.number,
            l.text = lit.text,
            l.author = lit.author,
            l.title = lit.title,
            l.publication = lit.publication,
            l.source = lit.source
        """
        
        self.conn.execute_query(query, {"literature": literature})
    
    def link_formulas_to_symbols(self):
        """Создать связи USES_SYMBOL между формулами и символами"""
        logger.info("Linking formulas to symbols...")
        
        query = """
        MATCH (f:Formula)
        WHERE size(f.symbols) > 0
        UNWIND f.symbols AS symbol_id
        MATCH (s:Symbol {id: symbol_id})
        MERGE (f)-[:USES_SYMBOL]->(s)
        """
        
        result = self.conn.execute_write(query)
        logger.info(f"Created {result['relationships_created']} USES_SYMBOL relationships")
