"""
Модели узлов графа
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class Book:
    """Книга"""
    id: str
    title: str
    author: str
    description: str


@dataclass
class Chapter:
    """Глава"""
    id: str
    title: str
    order: int
    file_path: str
    book_id: str


@dataclass
class Section:
    """Параграф/Раздел"""
    id: str
    title: str
    number: str
    order: int
    file_path: str
    position: int
    chapter_id: str


@dataclass
class Subsection:
    """Подраздел"""
    id: str
    title: str
    level: str
    order: int
    section_id: str


@dataclass
class Paragraph:
    """Абзац/Текстовый блок"""
    id: str
    content: str
    order: int
    word_count: int
    parent_id: str  # section_id или subsection_id


@dataclass
class Formula:
    """Формула"""
    id: str
    type: str  # inline | block
    latex: str
    metadata: Dict[str, Any]
    source: Dict[str, Any]
    symbols: List[str] = field(default_factory=list)
    wrapper_html: Optional[str] = None


@dataclass
class Illustration:
    """Иллюстрация"""
    id: str
    type: str
    svg_content: str
    caption: str
    metadata: Dict[str, Any]
    source: Dict[str, Any]
    wrapper_html: Optional[str] = None


@dataclass
class Table:
    """Таблица"""
    id: str
    type: str
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    source: Dict[str, Any]
    html_attributes: Optional[Dict[str, str]] = None


@dataclass
class Literature:
    """Литература"""
    id: str
    number: int
    text: str
    author: str
    title: str
    publication: str
    source: Dict[str, Any]


@dataclass
class Concept:
    """Концепция/Термин"""
    id: str
    name: str
    definition: str
    aliases: List[str] = field(default_factory=list)
    category: Optional[str] = None
