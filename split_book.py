#!/usr/bin/env python3
import os
import re
import shutil
import yaml
from collections import defaultdict

# Функция для очистки заголовков от HTML-тегов
def clean_header(header):
    # Удаляем HTML теги
    cleaned = re.sub(r'<[^>]+>', '', header)
    # Заменяем специальные символы
    cleaned = cleaned.replace('&', '&amp;')
    # Убираем лишние пробелы
    cleaned = ' '.join(cleaned.split())
    return cleaned

# Функция для создания безопасного имени файла
def make_safe_filename(text):
    # Удаляем HTML теги
    text = re.sub(r'<[^>]+>', '', text)
    # Преобразуем в нижний регистр
    text = text.lower()
    # Заменяем пробелы и специальные символы на дефис
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

# Функция для разделения файла на части и создания структуры
def split_book(input_file, output_dir):
    # Проверяем и создаем выходную директорию, если её нет
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Читаем содержимое файла
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Регулярное выражение для поиска заголовков
    h1_pattern = r'^#\s+(.+?)\s*$'
    h2_pattern = r'^##\s+(.+?)\s*$'
    h3_pattern = r'^###\s+(.+?)\s*$'

    # Запускаем поиск заголовков
    h1_matches = list(re.finditer(h1_pattern, content, re.MULTILINE))
    h2_matches = list(re.finditer(h2_pattern, content, re.MULTILINE))
    h3_matches = list(re.finditer(h3_pattern, content, re.MULTILINE))
    
    # Список для хранения информации о главах
    chapters = []
    
    # Обрабатываем каждую главу
    for i, h1_match in enumerate(h1_matches):
        h1_title = h1_match.group(1)
        h1_start = h1_match.start()
        
        # Определяем конец главы (начало следующей главы или конец файла)
        h1_end = len(content)
        if i < len(h1_matches) - 1:
            h1_end = h1_matches[i + 1].start()
        
        # Создаем директорию для главы
        chapter_dir = f"chapter_{make_safe_filename(h1_title)}"
        chapter_path = os.path.join(output_dir, chapter_dir)
        if not os.path.exists(chapter_path):
            os.makedirs(chapter_path)
        
        # Находим все параграфы (h2) в этой главе
        chapter_h2s = [m for m in h2_matches if h1_start < m.start() < h1_end]
        
        # Если в главе нет параграфов, сохраняем всю главу в один файл
        if not chapter_h2s:
            chapter_content = content[h1_start:h1_end]
            with open(os.path.join(chapter_path, 'index.md'), 'w', encoding='utf-8') as f:
                f.write(chapter_content)
            
            # Добавляем информацию о главе
            chapters.append({
                "title": clean_header(h1_title),
                "file": f"{chapter_dir}/index.md",
                "paragraphs": []
            })
            continue
        
        # Содержимое от начала главы до первого параграфа
        intro_content = content[h1_start:chapter_h2s[0].start()]
        
        # Обрабатываем параграфы в главе
        paragraphs = []
        for j, h2_match in enumerate(chapter_h2s):
            h2_title = h2_match.group(1)
            h2_start = h2_match.start()
            
            # Определяем конец параграфа (начало следующего параграфа, следующей главы или конец файла)
            h2_end = h1_end
            if j < len(chapter_h2s) - 1:
                h2_end = chapter_h2s[j + 1].start()
            
            # Создаем имя файла для параграфа
            paragraph_filename = f"{make_safe_filename(h2_title)}.md"
            paragraph_path = os.path.join(chapter_path, paragraph_filename)
            
            # Получаем содержимое параграфа
            paragraph_content = content[h2_start:h2_end]
            
            # Находим все подзаголовки (h3) в этом параграфе
            paragraph_h3s = [m for m in h3_matches if h2_start < m.start() < h2_end]
            
            # Записываем параграф в файл
            with open(paragraph_path, 'w', encoding='utf-8') as f:
                f.write(paragraph_content)
            
            # Добавляем информацию о параграфе
            paragraphs.append({
                "title": clean_header(h2_title),
                "file": f"{chapter_dir}/{paragraph_filename}"
            })
        
        # Создаем индексный файл для главы, содержащий введение и ссылки на параграфы
        with open(os.path.join(chapter_path, 'index.md'), 'w', encoding='utf-8') as f:
            f.write(intro_content)
            
            # Если введение не содержит заголовка главы, добавляем его
            if not intro_content.strip().startswith('# '):
                f.write(f"\n\n# {h1_title}\n\n")
                
            f.write("\n\n## Параграфы в этой главе\n\n")
            for p in paragraphs:
                # Получаем имя файла из пути
                fname = os.path.basename(p["file"])
                f.write(f"- [{p['title']}](./{fname})\n")
        
        # Добавляем информацию о главе
        chapters.append({
            "title": clean_header(h1_title),
            "file": f"{chapter_dir}/index.md",
            "paragraphs": paragraphs
        })
    
    # Создаем индексную страницу с содержанием
    with open(os.path.join(output_dir, 'index.md'), 'w', encoding='utf-8') as f:
        f.write('# Физика Базиева\n\n')
        f.write('## Система новейших фундаментальных открытий\n\n')
        f.write('### Содержание\n\n')
        
        for chapter in chapters:
            f.write(f"- [{chapter['title']}](./{chapter['file']})\n")
            for p in chapter['paragraphs']:
                f.write(f"  - [{p['title']}](./{p['file']})\n")
    
    # Возвращаем структуру для mkdocs.yml
    nav = []
    nav.append({"Главная": "index.md"})
    
    for chapter in chapters:
        chapter_nav = {clean_header(chapter['title']): []}
        chapter_nav[clean_header(chapter['title'])].append({"Обзор": chapter['file']})
        
        for p in chapter['paragraphs']:
            chapter_nav[clean_header(chapter['title'])].append({clean_header(p['title']): p['file']})
        
        nav.append(chapter_nav)
    
    return nav

# Функция для создания mkdocs.yml
def create_mkdocs_yml(nav):
    mkdocs_config = {
        "site_name": "Физика Базиева",
        "site_description": "Система новейших фундаментальных открытий",
        "theme": {
            "name": "material",
            "language": "ru",
            "features": [
                "navigation.sections",
                "navigation.indexes",
                "navigation.top",
                "search.highlight",
                "search.share"
            ],
            "palette": {
                "primary": "indigo",
                "accent": "indigo"
            }
        },
        "markdown_extensions": [
            {
                "pymdownx.arithmatex": {
                    "generic": True
                }
            },
            "pymdownx.highlight",
            "pymdownx.superfences",
            "pymdownx.details",
            "pymdownx.tabbed",
            "admonition",
            "attr_list",
            "md_in_html"
        ],
        "extra_javascript": [
            "https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"
        ],
        "plugins": [
            "search"
        ],
        "nav": nav
    }
    
    with open('mkdocs.yml', 'w', encoding='utf-8') as f:
        yaml.dump(mkdocs_config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

# Основная функция
def main():
    input_file = 'baziev_physics.md'
    output_dir = 'docs'
    
    # Создаем структуру проекта
    nav = split_book(input_file, output_dir)
    
    # Создаем mkdocs.yml
    create_mkdocs_yml(nav)
    
    print("Готово! Структура проекта создана успешно.")

if __name__ == "__main__":
    main()
