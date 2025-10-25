"""
Импортер структурных узлов (Book, Chapter, Section)
"""
import os
import logging
from pathlib import Path
from typing import List, Dict
from ..utils.neo4j_connection import Neo4jConnection
from ..models.nodes import Book, Chapter

logger = logging.getLogger(__name__)


class StructureImporter:
    """Импортер структуры книги"""
    
    def __init__(self, neo4j_conn: Neo4jConnection, config: Dict):
        self.conn = neo4j_conn
        self.config = config
        self.docs_path = Path(config["paths"]["docs"])
    
    def import_book(self):
        """Импортировать узел Book"""
        book = Book(
            id=self.config["book"]["id"],
            title=self.config["book"]["title"],
            author=self.config["book"]["author"],
            description=self.config["book"]["description"]
        )
        
        query = """
        MERGE (b:Book {id: $id})
        SET b.title = $title,
            b.author = $author,
            b.description = $description
        RETURN b
        """
        
        self.conn.execute_query(query, {
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "description": book.description
        })
        
        logger.info(f"Imported Book: {book.title}")
    
    def import_chapters(self):
        """Импортировать главы из структуры директорий"""
        chapters = self._scan_chapters()
        
        for chapter in chapters:
            query = """
            MERGE (ch:Chapter {id: $id})
            SET ch.title = $title,
                ch.order = $order,
                ch.file_path = $file_path
            WITH ch
            MATCH (b:Book {id: $book_id})
            MERGE (b)-[:HAS_CHAPTER {order: $order}]->(ch)
            RETURN ch
            """
            
            self.conn.execute_query(query, {
                "id": chapter.id,
                "title": chapter.title,
                "order": chapter.order,
                "file_path": chapter.file_path,
                "book_id": chapter.book_id
            })
            
            logger.info(f"Imported Chapter: {chapter.title}")
        
        # Создать связи NEXT/PREVIOUS между главами
        self._create_sequential_links(chapters, "Chapter")
    
    def _scan_chapters(self) -> List[Chapter]:
        """Сканировать директории и извлечь главы"""
        chapters = []
        chapter_dirs = sorted([
            d for d in self.docs_path.iterdir()
            if d.is_dir() and d.name.startswith("chapter_")
        ])
        
        for i, chapter_dir in enumerate(chapter_dirs):
            chapter_id = chapter_dir.name
            
            # Читаем index.md для получения названия
            index_path = chapter_dir / "index.md"
            title = self._extract_title_from_markdown(index_path)
            
            if not title:
                title = chapter_dir.name.replace("chapter_", "").replace("-", " ").title()
            
            chapters.append(Chapter(
                id=chapter_id,
                title=title,
                order=i + 1,
                file_path=str(chapter_dir.relative_to(self.docs_path.parent)),
                book_id=self.config["book"]["id"]
            ))
        
        return chapters
    
    def _extract_title_from_markdown(self, file_path: Path) -> str:
        """Извлечь заголовок из markdown файла"""
        if not file_path.exists():
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("# "):
                        return line[2:].strip()
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return ""
    
    def _create_sequential_links(self, items: List, label: str):
        """Создать последовательные связи NEXT/PREVIOUS"""
        for i in range(len(items) - 1):
            query = f"""
            MATCH (a:{label} {{id: $id1}})
            MATCH (b:{label} {{id: $id2}})
            MERGE (a)-[:NEXT]->(b)
            MERGE (b)-[:PREVIOUS]->(a)
            """
            
            self.conn.execute_query(query, {
                "id1": items[i].id,
                "id2": items[i + 1].id
            })
