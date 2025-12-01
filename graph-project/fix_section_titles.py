#!/usr/bin/env python3
"""
Скрипт для исправления заголовков секций в базе данных Neo4j.
Читает оригинальные заголовки из файлов docs/*.md и обновляет их в БД.
"""

import os
import re
import yaml
from pathlib import Path
from neo4j import GraphDatabase


def load_config():
    """Загружает конфигурацию из config.yml"""
    config_path = Path(__file__).parent / "config" / "config.yml"
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def extract_section_title_from_file(file_path):
    """Извлекает заголовок секции из файла markdown"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Ищем заголовок вида ## § 1. Название секции
            match = re.search(r'^##\s+(§\s*\d+\.?\d*\.?\s+.+?)$', content, re.MULTILINE)
            if match:
                title = match.group(1).strip()
                # Удаляем "§ " в начале и возвращаем остальное
                title = re.sub(r'^§\s*', '', title)
                return title
            
            # Для файлов без § (например, приложения, предисловие)
            match = re.search(r'^##\s+(.+?)$', content, re.MULTILINE)
            if match:
                return match.group(1).strip()
                
    except Exception as e:
        print(f"Ошибка чтения файла {file_path}: {e}")
    
    return None


def extract_titles_from_index(index_path):
    """Извлекает заголовки из index.md (содержание книги)"""
    titles_map = {}
    
    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Ищем все ссылки вида [§ 1. Название](путь/к/файлу.md)
        pattern = r'\[§\s*(\d+\.?\d*\.?)\s+(.+?)\]\(\./(.+?)\.md\)'
        matches = re.finditer(pattern, content)
        
        for match in matches:
            section_num = match.group(1)
            title = match.group(2).strip()
            file_path = match.group(3)
            
            # Формируем полный заголовок с номером
            full_title = f"{section_num} {title}"
            
            # ID секции - это последняя часть пути
            section_slug = file_path.split('/')[-1]
            chapter_slug = file_path.split('/')[0] if '/' in file_path else None
            
            if chapter_slug:
                section_id = f"{chapter_slug}_{section_slug}"
                titles_map[section_id] = full_title
    
    return titles_map


def build_section_id(chapter_slug, section_slug):
    """Строит ID секции из slug'ов главы и секции"""
    return f"{chapter_slug}_{section_slug}"


def scan_docs_directory(docs_path):
    """Сканирует директорию docs и извлекает все заголовки секций"""
    titles_map = {}
    
    docs_dir = Path(docs_path)
    
    # Проходим по всем директориям глав
    for chapter_dir in docs_dir.glob("chapter_*"):
        if not chapter_dir.is_dir():
            continue
            
        chapter_slug = chapter_dir.name
        
        # Проходим по всем файлам секций в главе
        for section_file in chapter_dir.glob("*.md"):
            if section_file.name == "index.md":
                continue
                
            section_slug = section_file.stem
            section_id = build_section_id(chapter_slug, section_slug)
            
            # Извлекаем заголовок из файла
            title = extract_section_title_from_file(section_file)
            if title:
                titles_map[section_id] = title
                print(f"✓ {section_id}: {title}")
            else:
                print(f"✗ Не удалось извлечь заголовок из {section_file}")
    
    return titles_map


def update_section_titles(driver, titles_map, dry_run=True):
    """Обновляет заголовки секций в Neo4j"""
    
    updated_count = 0
    not_found_count = 0
    
    with driver.session() as session:
        # Получаем все секции из БД
        result = session.run("MATCH (s:Section) RETURN s.id AS id, s.title AS current_title")
        
        for record in result:
            section_id = record["id"]
            current_title = record["current_title"]
            
            if section_id in titles_map:
                new_title = titles_map[section_id]
                
                if current_title != new_title:
                    print(f"\nОбновление секции: {section_id}")
                    print(f"  Было:  {current_title}")
                    print(f"  Стало: {new_title}")
                    
                    if not dry_run:
                        session.run(
                            "MATCH (s:Section {id: $id}) SET s.title = $title",
                            id=section_id,
                            title=new_title
                        )
                    
                    updated_count += 1
            else:
                print(f"\n⚠ Секция не найдена в исходниках: {section_id}")
                print(f"   Текущий заголовок: {current_title}")
                not_found_count += 1
    
    print(f"\n{'=' * 70}")
    print(f"Результаты:")
    print(f"  Обновлено: {updated_count}")
    print(f"  Не найдено в исходниках: {not_found_count}")
    
    if dry_run:
        print(f"\n⚠ Режим DRY RUN - изменения НЕ применены")
        print(f"Для применения изменений запустите с аргументом --apply")
    else:
        print(f"\n✓ Изменения успешно применены к базе данных")


def main():
    import sys
    
    # Проверяем аргументы
    dry_run = "--apply" not in sys.argv
    
    print("Загрузка конфигурации...")
    config = load_config()
    
    # Путь к docs
    docs_path = Path(__file__).parent / ".." / "docs"
    print(f"Сканирование директории: {docs_path}")
    
    # Извлекаем заголовки из файлов
    titles_map = scan_docs_directory(docs_path)
    
    print(f"\nНайдено заголовков: {len(titles_map)}")
    
    # Подключаемся к Neo4j
    print("\nПодключение к Neo4j...")
    neo4j_config = config['neo4j']
    driver = GraphDatabase.driver(
        neo4j_config['uri'],
        auth=(neo4j_config['username'], neo4j_config['password'])
    )
    
    try:
        # Обновляем заголовки
        update_section_titles(driver, titles_map, dry_run=dry_run)
    finally:
        driver.close()


if __name__ == "__main__":
    main()
