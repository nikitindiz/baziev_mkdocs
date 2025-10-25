"""
Импортер параграфов из markdown файлов и связывание контента
"""
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm
from ..utils.neo4j_connection import Neo4jConnection

logger = logging.getLogger(__name__)


class ContentLinker:
    """Импортер параграфов и связывание контента"""
    
    def __init__(self, neo4j_conn: Neo4jConnection, config: Dict):
        self.conn = neo4j_conn
        self.config = config
        self.docs_path = Path(config["paths"]["docs"])
        
        # Регулярные выражения для поиска вложений
        self.formula_pattern = re.compile(r'\{\{formula:([a-f0-9]{12})\}\}')
        self.symbol_pattern = re.compile(r'\{\{symbol:([a-f0-9]{12})\}\}')
        self.illustration_pattern = re.compile(r'\{\{illustration:([a-f0-9]{12})\}\}')
        self.table_pattern = re.compile(r'\{\{table:([a-f0-9]{12})\}\}')
        self.literature_pattern = re.compile(r'\{\{literature:([a-f0-9]{12})\}\}')
    
    def import_sections_and_paragraphs(self):
        """Импортировать секции и параграфы из markdown файлов"""
        logger.info("Importing sections and paragraphs from markdown files...")
        
        # Получить список всех глав
        chapters = self._get_chapters()
        
        for chapter in tqdm(chapters):
            chapter_dir = self.docs_path / chapter['id']
            
            # Обработать все markdown файлы в главе
            md_files = sorted(chapter_dir.glob("*.md"))
            
            section_order = 1
            for md_file in md_files:
                if md_file.name == "index.md":
                    continue
                
                self._process_markdown_file(md_file, chapter['id'], section_order)
                section_order += 1
        
        logger.info("Sections and paragraphs import completed!")
    
    def _get_chapters(self) -> List[Dict]:
        """Получить список всех глав из графа"""
        query = "MATCH (ch:Chapter) RETURN ch.id as id, ch.order as order ORDER BY ch.order"
        return self.conn.execute_query(query)
    
    def _process_markdown_file(self, file_path: Path, chapter_id: str, section_order: int):
        """Обработать markdown файл и извлечь секции и параграфы"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return
        
        # Извлечь заголовок секции (первый # заголовок)
        lines = content.split('\n')
        section_title = None
        section_number = None
        
        for line in lines:
            if line.startswith('# '):
                section_title = line[2:].strip()
                # Попытаться извлечь номер параграфа (§ 1, § 2, и т.д.)
                match = re.match(r'§\s*(\d+)', section_title)
                if match:
                    section_number = f"§ {match.group(1)}"
                break
        
        if not section_title:
            section_title = file_path.stem.replace('-', ' ').title()
            section_number = f"§ {section_order}"
        
        # Создать секцию
        section_id = f"{chapter_id}_{file_path.stem}"
        self._create_section(section_id, section_title, section_number, 
                            section_order, str(file_path), chapter_id)
        
        # Извлечь параграфы (блоки текста между заголовками и пустыми строками)
        paragraphs = self._extract_paragraphs(content)
        
        # Создать параграфы
        for i, para_content in enumerate(paragraphs):
            if para_content.strip():
                self._create_paragraph(f"{section_id}_p{i}", para_content, 
                                      i + 1, section_id)
    
    def _create_section(self, section_id: str, title: str, number: str, 
                       order: int, file_path: str, chapter_id: str):
        """Создать секцию в графе"""
        query = """
        MERGE (s:Section {id: $id})
        SET s.title = $title,
            s.number = $number,
            s.order = $order,
            s.file_path = $file_path
        WITH s
        MATCH (ch:Chapter {id: $chapter_id})
        MERGE (ch)-[:HAS_SECTION {order: $order}]->(s)
        """
        
        self.conn.execute_query(query, {
            "id": section_id,
            "title": title,
            "number": number,
            "order": order,
            "file_path": file_path,
            "chapter_id": chapter_id
        })
    
    def _create_paragraph(self, para_id: str, content: str, order: int, section_id: str):
        """Создать параграф в графе"""
        word_count = len(content.split())
        
        query = """
        MERGE (p:Paragraph {id: $id})
        SET p.content = $content,
            p.order = $order,
            p.word_count = $word_count
        WITH p
        MATCH (s:Section {id: $section_id})
        MERGE (s)-[:HAS_PARAGRAPH {order: $order}]->(p)
        """
        
        self.conn.execute_query(query, {
            "id": para_id,
            "content": content,
            "order": order,
            "word_count": word_count,
            "section_id": section_id
        })
    
    def _extract_paragraphs(self, content: str) -> List[str]:
        """Извлечь параграфы из текста"""
        # Разделить по двойным переводам строки
        blocks = re.split(r'\n\n+', content)
        
        paragraphs = []
        for block in blocks:
            block = block.strip()
            
            # Пропустить заголовки и пустые блоки
            if not block or block.startswith('#'):
                continue
            
            # Пропустить блоки с HTML тегами (но сохраняем блоки с {{references}})
            if block.startswith('<'):
                continue
            
            # Сохраняем блоки с ссылками на артефакты ({{table:id}}, {{formula:id}}, etc.)
            # Они важны для связывания контента с параграфами
            paragraphs.append(block)
        
        return paragraphs
    
    def link_content(self):
        """Связать контент (формулы, символы, иллюстрации, таблицы, литература) с параграфами"""
        logger.info("Linking content to paragraphs...")
        
        # Получить все параграфы
        query = "MATCH (p:Paragraph) RETURN p.id as id, p.content as content"
        paragraphs = self.conn.execute_query(query)
        
        for para in tqdm(paragraphs):
            self._link_paragraph_content(para['id'], para['content'])
        
        logger.info("Content linking completed!")
    
    def link_paragraph_sequence(self):
        """Создать связи NEXT между последовательными параграфами"""
        logger.info("Linking paragraph sequence...")
        
        # Получить все секции
        query = """
        MATCH (s:Section)
        RETURN s.id as section_id
        ORDER BY s.order
        """
        sections = self.conn.execute_query(query)
        
        total_links = 0
        for section in tqdm(sections):
            # Получить параграфы секции в порядке их следования
            para_query = """
            MATCH (s:Section {id: $section_id})-[:HAS_PARAGRAPH]->(p:Paragraph)
            RETURN p.id as id, p.order as order
            ORDER BY p.order
            """
            paragraphs = self.conn.execute_query(para_query, {"section_id": section['section_id']})
            
            # Создать связи NEXT между последовательными параграфами
            for i in range(len(paragraphs) - 1):
                current_id = paragraphs[i]['id']
                next_id = paragraphs[i + 1]['id']
                
                link_query = """
                MATCH (p1:Paragraph {id: $current_id})
                MATCH (p2:Paragraph {id: $next_id})
                MERGE (p1)-[:NEXT]->(p2)
                """
                self.conn.execute_query(link_query, {
                    "current_id": current_id,
                    "next_id": next_id
                })
                total_links += 1
        
        logger.info(f"Created {total_links} NEXT relationships between paragraphs")
        
        # Также создать связи NEXT между секциями
        self._link_section_sequence()
    
    def _link_section_sequence(self):
        """Создать связи NEXT между последовательными секциями"""
        logger.info("Linking section sequence...")
        
        # Получить все главы
        query = """
        MATCH (ch:Chapter)
        RETURN ch.id as chapter_id
        ORDER BY ch.order
        """
        chapters = self.conn.execute_query(query)
        
        total_links = 0
        for chapter in chapters:
            # Получить секции главы в порядке их следования
            section_query = """
            MATCH (ch:Chapter {id: $chapter_id})-[:HAS_SECTION]->(s:Section)
            RETURN s.id as id, s.order as order
            ORDER BY s.order
            """
            sections = self.conn.execute_query(section_query, {"chapter_id": chapter['chapter_id']})
            
            # Создать связи NEXT между последовательными секциями
            for i in range(len(sections) - 1):
                current_id = sections[i]['id']
                next_id = sections[i + 1]['id']
                
                link_query = """
                MATCH (s1:Section {id: $current_id})
                MATCH (s2:Section {id: $next_id})
                MERGE (s1)-[:NEXT]->(s2)
                """
                self.conn.execute_query(link_query, {
                    "current_id": current_id,
                    "next_id": next_id
                })
                total_links += 1
        
        logger.info(f"Created {total_links} NEXT relationships between sections")
    
    def _link_paragraph_content(self, para_id: str, content: str):
        """Связать контент параграфа"""
        position = 0
        
        # Формулы
        for match in self.formula_pattern.finditer(content):
            formula_id = match.group(1)
            self._create_contains_formula_link(para_id, formula_id, match.start())
        
        # Иллюстрации
        for match in self.illustration_pattern.finditer(content):
            illustration_id = match.group(1)
            self._create_contains_illustration_link(para_id, illustration_id, match.start())
        
        # Таблицы
        for match in self.table_pattern.finditer(content):
            table_id = match.group(1)
            self._create_contains_table_link(para_id, table_id, match.start())
        
        # Литература
        for match in self.literature_pattern.finditer(content):
            literature_id = match.group(1)
            self._create_cites_link(para_id, literature_id, match.start())
    
    def _create_contains_formula_link(self, para_id: str, formula_id: str, position: int):
        """Создать связь CONTAINS_FORMULA"""
        query = """
        MATCH (p:Paragraph {id: $para_id})
        MATCH (f:Formula {id: $formula_id})
        MERGE (p)-[r:CONTAINS_FORMULA]->(f)
        SET r.position = $position
        """
        self.conn.execute_query(query, {
            "para_id": para_id,
            "formula_id": formula_id,
            "position": position
        })
    
    def _create_contains_illustration_link(self, para_id: str, illustration_id: str, position: int):
        """Создать связь CONTAINS_ILLUSTRATION"""
        query = """
        MATCH (p:Paragraph {id: $para_id})
        MATCH (i:Illustration {id: $illustration_id})
        MERGE (p)-[r:CONTAINS_ILLUSTRATION]->(i)
        SET r.position = $position
        """
        self.conn.execute_query(query, {
            "para_id": para_id,
            "illustration_id": illustration_id,
            "position": position
        })
    
    def _create_contains_table_link(self, para_id: str, table_id: str, position: int):
        """Создать связь CONTAINS_TABLE"""
        query = """
        MATCH (p:Paragraph {id: $para_id})
        MATCH (t:Table {id: $table_id})
        MERGE (p)-[r:CONTAINS_TABLE]->(t)
        SET r.position = $position
        """
        self.conn.execute_query(query, {
            "para_id": para_id,
            "table_id": table_id,
            "position": position
        })
    
    def _create_cites_link(self, para_id: str, literature_id: str, position: int):
        """Создать связь CITES"""
        query = """
        MATCH (p:Paragraph {id: $para_id})
        MATCH (l:Literature {id: $literature_id})
        MERGE (p)-[r:CITES]->(l)
        SET r.position = $position
        """
        self.conn.execute_query(query, {
            "para_id": para_id,
            "literature_id": literature_id,
            "position": position
        })
    
    def link_orphan_artifacts_to_sections(self):
        """Связать артефакты без параграфов напрямую с секциями на основе source файла"""
        logger.info("Linking orphan artifacts to sections...")
        
        # Найти таблицы без связей с параграфами
        query = """
        MATCH (t:Table)
        WHERE NOT exists((:Paragraph)-[:CONTAINS_TABLE]->(t))
        RETURN t.id as id, t.source as source
        """
        
        orphan_tables = self.conn.execute_query(query)
        
        logger.info(f"Found {len(orphan_tables)} tables without paragraph links")
        
        linked_count = 0
        for table in orphan_tables:
            table_id = table['id']
            source = table.get('source')
            
            if not source:
                continue
            
            # source - это JSON строка, нужно распарсить
            import json
            try:
                source_data = json.loads(source) if isinstance(source, str) else source
                file_path = source_data.get('file', '')
                
                # Извлечь chapter_id из пути файла
                # Пример: "chapter_приложение-3-периодическая-система-элементов/index.md"
                if '/' in file_path:
                    parts = file_path.split('/')
                    chapter_id = parts[0]  # chapter_приложение-3-периодическая-система-элементов
                    file_name = parts[1].replace('.md', '')  # index
                    section_id = f"{chapter_id}_{file_name}"
                    
                    # Попробовать связать с секцией
                    link_query = """
                    MATCH (s:Section {id: $section_id})
                    MATCH (t:Table {id: $table_id})
                    MERGE (s)-[r:CONTAINS_TABLE]->(t)
                    SET r.orphan = true
                    RETURN count(s) as linked
                    """
                    
                    result = self.conn.execute_query(link_query, {
                        "section_id": section_id,
                        "table_id": table_id
                    })
                    
                    if result and result[0]['linked'] > 0:
                        linked_count += 1
                        logger.debug(f"Linked orphan table {table_id} to section {section_id}")
                    else:
                        # Если секция не найдена, связываем с главой
                        link_query = """
                        MATCH (c:Chapter {id: $chapter_id})
                        MATCH (t:Table {id: $table_id})
                        MERGE (c)-[r:CONTAINS_TABLE]->(t)
                        SET r.orphan = true
                        """
                        
                        self.conn.execute_query(link_query, {
                            "chapter_id": chapter_id,
                            "table_id": table_id
                        })
                        
                        linked_count += 1
                        logger.debug(f"Linked orphan table {table_id} to chapter {chapter_id}")
                    
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.warning(f"Could not parse source for table {table_id}: {e}")
        
        logger.info(f"Linked {linked_count} orphan tables to sections")
        
        # То же самое для иллюстраций
        query = """
        MATCH (i:Illustration)
        WHERE NOT exists((:Paragraph)-[:CONTAINS_ILLUSTRATION]->(i))
        RETURN i.id as id, i.source as source
        """
        
        orphan_illustrations = self.conn.execute_query(query)
        
        logger.info(f"Found {len(orphan_illustrations)} illustrations without paragraph links")
        
        linked_count = 0
        for illust in orphan_illustrations:
            illust_id = illust['id']
            source = illust.get('source')
            
            if not source:
                continue
            
            import json
            try:
                source_data = json.loads(source) if isinstance(source, str) else source
                file_path = source_data.get('file', '')
                
                if '/' in file_path:
                    parts = file_path.split('/')
                    chapter_id = parts[0]
                    file_name = parts[1].replace('.md', '')
                    section_id = f"{chapter_id}_{file_name}"
                    
                    # Попробовать связать с секцией
                    link_query = """
                    MATCH (s:Section {id: $section_id})
                    MATCH (i:Illustration {id: $illust_id})
                    MERGE (s)-[r:CONTAINS_ILLUSTRATION]->(i)
                    SET r.orphan = true
                    RETURN count(s) as linked
                    """
                    
                    result = self.conn.execute_query(link_query, {
                        "section_id": section_id,
                        "illust_id": illust_id
                    })
                    
                    if result and result[0]['linked'] > 0:
                        linked_count += 1
                        logger.debug(f"Linked orphan illustration {illust_id} to section {section_id}")
                    else:
                        # Если секция не найдена, связываем с главой
                        link_query = """
                        MATCH (c:Chapter {id: $chapter_id})
                        MATCH (i:Illustration {id: $illust_id})
                        MERGE (c)-[r:CONTAINS_ILLUSTRATION]->(i)
                        SET r.orphan = true
                        """
                        
                        self.conn.execute_query(link_query, {
                            "chapter_id": chapter_id,
                            "illust_id": illust_id
                        })
                        
                        linked_count += 1
                        logger.debug(f"Linked orphan illustration {illust_id} to chapter {chapter_id}")
                    
            except (json.JSONDecodeError, KeyError, AttributeError) as e:
                logger.warning(f"Could not parse source for illustration {illust_id}: {e}")
        
        logger.info(f"Linked {linked_count} orphan illustrations to sections")

