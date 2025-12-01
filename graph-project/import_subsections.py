#!/usr/bin/env python3
"""
Импорт подразделов (заголовков третьего уровня ###) в граф базы данных.

Этот скрипт:
1. Извлекает заголовки ### из normalized markdown файлов
2. Создает узлы Subsection в Neo4j
3. Связывает их с существующими Section узлами
4. Переназначает существующие Paragraph узлы к соответствующим Subsection

ВАЖНО: Скрипт НЕ изменяет содержимое существующих узлов Paragraph,
только создает новую структуру и связи.
"""

import re
import sys
from pathlib import Path
from typing import List, Dict, Optional

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    def tqdm(iterable, desc=None):
        """Простая замена tqdm если библиотека не установлена"""
        if desc:
            print(f"{desc}...")
        return iterable

# Добавляем путь к модулям проекта
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.neo4j_connection import Neo4jConnection
import yaml

def load_config(config_path: str) -> dict:
    """Загрузить конфигурацию из YAML файла"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


class SubsectionImporter:
    """Импортер подразделов из markdown файлов"""
    
    def __init__(self, neo4j_conn: Neo4jConnection, config: Dict, dry_run: bool = False):
        self.conn = neo4j_conn
        self.config = config
        self.normalized_path = Path(config["paths"]["normalized"])
        self.dry_run = dry_run
        
        # Паттерн для заголовков третьего уровня
        # Примеры: ### 1. Название, ### 2. Название и т.д.
        self.subsection_pattern = re.compile(r'^###\s+(\d+)\.\s+(.+)$', re.MULTILINE)
        
        # Паттерн для заголовка секции (параграфа)
        self.section_pattern = re.compile(r'^##\s+(.+)$', re.MULTILINE)
    
    def run(self):
        """Основной метод выполнения импорта"""
        print("=" * 80)
        if self.dry_run:
            print("ИМПОРТ ПОДРАЗДЕЛОВ (SUBSECTIONS) - DRY RUN РЕЖИМ")
            print("=" * 80)
            print("⚠️  Изменения НЕ будут сохранены в базу данных")
        else:
            print("ИМПОРТ ПОДРАЗДЕЛОВ (SUBSECTIONS)")
            print("=" * 80)
        print()
        
        # Шаг 1: Создать constraint для Subsection
        self._create_constraints()
        
        # Шаг 2: Получить все Section из базы
        sections = self._get_all_sections()
        print(f"Найдено секций в базе: {len(sections)}")
        print()
        
        # Шаг 3: Обработать каждую секцию
        total_subsections = 0
        total_reassigned_paragraphs = 0
        
        for section in tqdm(sections, desc="Обработка секций"):
            result = self._process_section(section)
            total_subsections += result['subsections_created']
            total_reassigned_paragraphs += result['paragraphs_reassigned']
        
        # Шаг 4: Создать NEXT/PREVIOUS связи между подразделами
        self._create_subsection_sequences()
        
        print()
        print("=" * 80)
        print("РЕЗУЛЬТАТЫ ИМПОРТА")
        print("=" * 80)
        print(f"Создано подразделов: {total_subsections}")
        print(f"Переназначено параграфов: {total_reassigned_paragraphs}")
        print()
    
    def _create_constraints(self):
        """Создать constraints для узлов Subsection"""
        print("Создание constraints для Subsection...")
        
        if self.dry_run:
            print("  [DRY RUN] Пропущено создание constraint")
            print()
            return
        
        query = """
        CREATE CONSTRAINT subsection_id IF NOT EXISTS 
        FOR (s:Subsection) REQUIRE s.id IS UNIQUE
        """
        
        try:
            self.conn.execute_query(query)
            print("✓ Constraint создан успешно")
        except Exception as e:
            print(f"⚠ Constraint уже существует или ошибка: {e}")
        print()
    
    def _get_all_sections(self) -> List[Dict]:
        """Получить все секции из базы данных"""
        query = """
        MATCH (s:Section)
        RETURN s.id as id, s.file_path as file_path, s.title as title
        ORDER BY s.id
        """
        
        return self.conn.execute_query(query)
    
    def _process_section(self, section: Dict) -> Dict:
        """
        Обработать одну секцию:
        1. Найти соответствующий markdown файл в normalized
        2. Извлечь заголовки ###
        3. Создать узлы Subsection
        4. Переназначить параграфы
        """
        section_id = section['id']
        file_path = section.get('file_path')
        
        result = {
            'subsections_created': 0,
            'paragraphs_reassigned': 0
        }
        
        if not file_path:
            return result
        
        # Найти файл в normalized директории
        normalized_file = self._find_normalized_file(file_path)
        
        if not normalized_file or not normalized_file.exists():
            return result
        
        # Прочитать файл
        try:
            content = normalized_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Ошибка чтения {normalized_file}: {e}")
            return result
        
        # Извлечь подразделы
        subsections = self._extract_subsections(content)
        
        if not subsections:
            return result
        
        # Создать узлы Subsection и связать с параграфами
        for i, subsection_info in enumerate(subsections):
            subsection_id = f"{section_id}_sub{subsection_info['number']}"
            
            # Создать узел Subsection
            self._create_subsection(
                subsection_id=subsection_id,
                number=subsection_info['number'],
                title=subsection_info['title'],
                order=i + 1,
                section_id=section_id
            )
            
            result['subsections_created'] += 1
            
            # Переназначить параграфы к этому подразделу
            # Параграфы между текущим подразделом и следующим принадлежат текущему
            start_pos = subsection_info['position']
            end_pos = subsections[i + 1]['position'] if i + 1 < len(subsections) else len(content)
            
            reassigned = self._reassign_paragraphs_to_subsection(
                section_id=section_id,
                subsection_id=subsection_id,
                start_pos=start_pos,
                end_pos=end_pos,
                content=content
            )
            
            result['paragraphs_reassigned'] += reassigned
        
        return result
    
    def _find_normalized_file(self, original_file_path: str) -> Optional[Path]:
        """
        Найти соответствующий файл в normalized директории.
        Ищем в step-05-extract-and-link-quoted-literature/result/
        """
        # Получаем имя файла
        file_path = Path(original_file_path)
        
        # Паттерн поиска в normalized
        search_pattern = f"**/step-05-extract-and-link-quoted-literature/result/**/{file_path.name}"
        
        matches = list(self.normalized_path.glob(search_pattern))
        
        if matches:
            return matches[0]
        
        return None
    
    def _extract_subsections(self, content: str) -> List[Dict]:
        """
        Извлечь все заголовки ### из содержимого файла.
        
        Возвращает список словарей с информацией о каждом подразделе:
        - number: номер подраздела (например, "1", "2")
        - title: полный заголовок (например, "Состояние термодинамики газов.")
        - position: позиция в тексте
        """
        subsections = []
        
        for match in self.subsection_pattern.finditer(content):
            subsections.append({
                'number': match.group(1),
                'title': match.group(2).strip(),
                'position': match.start(),
                'full_title': match.group(0).replace('###', '').strip()
            })
        
        return subsections
    
    def _create_subsection(
        self, 
        subsection_id: str, 
        number: str, 
        title: str, 
        order: int, 
        section_id: str
    ):
        """Создать узел Subsection и связать его с Section"""
        if self.dry_run:
            print(f"  [DRY RUN] Создание подраздела: {subsection_id} - {number}. {title}")
            return
        
        query = """
        MERGE (sub:Subsection {id: $subsection_id})
        SET sub.number = $number,
            sub.title = $title,
            sub.order = $order
        
        WITH sub
        MATCH (s:Section {id: $section_id})
        MERGE (s)-[:HAS_SUBSECTION {order: $order}]->(sub)
        """
        
        self.conn.execute_query(query, {
            'subsection_id': subsection_id,
            'number': number,
            'title': title,
            'order': order,
            'section_id': section_id
        })
    
    def _reassign_paragraphs_to_subsection(
        self,
        section_id: str,
        subsection_id: str,
        start_pos: int,
        end_pos: int,
        content: str
    ) -> int:
        """
        Переназначить параграфы к подразделу на основе их позиции в тексте.
        
        Стратегия:
        1. Получить все параграфы секции упорядоченные по order
        2. Определить, какие параграфы попадают в диапазон этого подраздела
        3. Создать связи CONTAINS_PARAGRAPH от Subsection к этим параграфам
        
        Возвращает количество переназначенных параграфов.
        """
        # Получить все параграфы секции
        paragraphs_query = """
        MATCH (s:Section {id: $section_id})-[:HAS_PARAGRAPH]->(p:Paragraph)
        RETURN p.id as id, p.order as order, p.content as content
        ORDER BY p.order
        """
        
        paragraphs = self.conn.execute_query(paragraphs_query, {'section_id': section_id})
        
        if not paragraphs:
            return 0
        
        # Извлечь текст подраздела
        subsection_content = content[start_pos:end_pos]
        
        # Подсчитать количество параграфов в этом подразделе
        # Простая эвристика: количество двойных переводов строк
        paragraph_count = len([p for p in subsection_content.split('\n\n') if p.strip()])
        
        # Переназначить параграфы
        reassigned = 0
        
        for i, paragraph in enumerate(paragraphs):
            if reassigned >= paragraph_count:
                break
            
            # Создать связь от Subsection к Paragraph
            if self.dry_run:
                print(f"    [DRY RUN] Связывание параграфа {paragraph['id']} с {subsection_id}")
            else:
                link_query = """
                MATCH (sub:Subsection {id: $subsection_id})
                MATCH (p:Paragraph {id: $paragraph_id})
                MERGE (sub)-[:CONTAINS_PARAGRAPH {order: $order}]->(p)
                """
                
                self.conn.execute_query(link_query, {
                    'subsection_id': subsection_id,
                    'paragraph_id': paragraph['id'],
                    'order': i + 1
                })
            
            reassigned += 1
        
        return reassigned
    
    def _create_subsection_sequences(self):
        """Создать NEXT/PREVIOUS связи между подразделами внутри каждой секции"""
        print()
        print("Создание последовательностей подразделов...")
        
        if self.dry_run:
            print("  [DRY RUN] Пропущено создание связей NEXT/PREVIOUS")
            print()
            return
        
        query = """
        MATCH (s:Section)-[:HAS_SUBSECTION]->(sub:Subsection)
        WITH s, sub
        ORDER BY s.id, sub.order
        WITH s, collect(sub) as subsections
        UNWIND range(0, size(subsections)-2) as i
        WITH subsections[i] as current, subsections[i+1] as next
        MERGE (current)-[:NEXT]->(next)
        MERGE (next)-[:PREVIOUS]->(current)
        RETURN count(*) as links_created
        """
        
        result = self.conn.execute_query(query)
        
        if result:
            print(f"✓ Создано {result[0]['links_created']} связей NEXT/PREVIOUS")
        print()


def main():
    """Главная функция"""
    import argparse
    
    # Парсинг аргументов командной строки
    parser = argparse.ArgumentParser(
        description='Импорт подразделов (заголовков ###) в Neo4j граф',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  # Dry-run режим (без изменений в БД)
  python import_subsections.py --dry-run
  
  # Реальный импорт
  python import_subsections.py
  
  # С указанием конфигурации
  python import_subsections.py --config /path/to/config.yml
        """
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Режим пробного запуска без сохранения в базу данных'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        default=None,
        help='Путь к файлу конфигурации (по умолчанию: config/config.yml)'
    )
    
    args = parser.parse_args()
    
    # Загрузить конфигурацию
    if args.config:
        config_path = Path(args.config)
    else:
        # Попробуем несколько вариантов расположения конфига
        possible_configs = [
            Path(__file__).parent / "config" / "config.yml",
            Path(__file__).parent / "config" / "config.yaml",
            Path(__file__).parent / "src" / "config" / "config.yaml",
        ]
        
        config_path = None
        for path in possible_configs:
            if path.exists():
                config_path = path
                break
        
        if not config_path:
            print("✗ Ошибка: файл конфигурации не найден!")
            print(f"  Проверенные пути:")
            for path in possible_configs:
                print(f"    - {path}")
            print()
            print("  Укажите путь к конфигурации через --config")
            sys.exit(1)
    
    print(f"Загрузка конфигурации: {config_path}")
    config = load_config(str(config_path))
    print()
    
    # Вывести информацию о подключении (без пароля)
    neo4j_config = config["neo4j"]
    print(f"Neo4j URI: {neo4j_config['uri']}")
    print(f"Database: {neo4j_config.get('database', 'neo4j')}")
    print(f"Username: {neo4j_config['username']}")
    print()
    
    if args.dry_run:
        print("🔍 Режим DRY-RUN активирован")
        print("   Изменения не будут сохранены в базу данных")
        print()
    
    # Подключиться к Neo4j
    try:
        neo4j_conn = Neo4jConnection(
            uri=neo4j_config['uri'],
            user=neo4j_config['username'],
            password=neo4j_config['password'],
            database=neo4j_config.get('database', 'neo4j')
        )
        print("✓ Подключение к Neo4j установлено")
        print()
    except Exception as e:
        print(f"✗ Ошибка подключения к Neo4j: {e}")
        print()
        print("Проверьте:")
        print("  1. Neo4j запущен и доступен")
        print("  2. Учетные данные в config.yml корректны")
        print("  3. URI правильный (bolt://localhost:7687)")
        sys.exit(1)
    
    try:
        # Создать импортер и запустить
        importer = SubsectionImporter(neo4j_conn, config, dry_run=args.dry_run)
        importer.run()
        
        if args.dry_run:
            print("✓ Dry-run завершен успешно!")
            print("  Для реального импорта запустите без флага --dry-run")
        else:
            print("✓ Импорт завершен успешно!")
        
    except Exception as e:
        print(f"✗ Ошибка при импорте: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        neo4j_conn.close()


if __name__ == "__main__":
    main()
