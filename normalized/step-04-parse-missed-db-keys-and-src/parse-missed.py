#!/usr/bin/env python3
"""
Step 04: Parse Missed DB Keys and SRC

Обрабатывает пропущенные div-обёртки с data-db-key и data-src после шага 03,
которые остались вокруг ссылок на формулы. Извлекает метаданные и обновляет
соответствующие JSON файлы формул.

Шаблон div-обёрток:
<div data-db-key="30" data-src="images/formula_full_2_9.webp">
{{formula:c6fed30764ee}}
</div>

Задача:
1. Скопировать файлы из step-03/result в step-04/result
2. Найти все такие div-обёртки в новых файлах
3. Извлечь formula_id из ссылки внутри
4. Обновить соответствующий JSON файл формулы метаданными
5. Удалить div-обёртку, оставив только ссылку на формулу
"""

import os
import re
import json
import shutil
from pathlib import Path
from typing import Dict, Tuple, Optional


def find_div_wrappers(content: str) -> list:
    """
    Находит все div-обёртки с data-db-key/data-src вокруг формул.
    
    Returns:
        List of tuples: (full_match, db_key, src, formula_id)
    """
    # Паттерн для div с метаданными, содержащий ссылку на формулу
    pattern = r'<div\s+data-db-key="([^"]+)"\s+data-src="([^"]+)">\s*\{\{formula:([a-f0-9]{12})\}\}\s*</div>'
    
    matches = []
    for match in re.finditer(pattern, content, re.DOTALL):
        full_match = match.group(0)
        db_key = match.group(1)
        src = match.group(2)
        formula_id = match.group(3)
        matches.append((full_match, db_key, src, formula_id))
    
    return matches


def update_formula_json(formula_id: str, db_key: str, src: str, formulas_dir: Path) -> bool:
    """
    Обновляет JSON файл формулы с метаданными.
    
    Returns:
        bool: True если файл был обновлён, False если не найден
    """
    formula_file = formulas_dir / f"formula_{formula_id}.json"
    
    if not formula_file.exists():
        print(f"  ⚠️  Файл формулы не найден: {formula_file.name}")
        return False
    
    # Читаем JSON
    with open(formula_file, 'r', encoding='utf-8') as f:
        formula_data = json.load(f)
    
    # Обновляем метаданные
    formula_data['metadata']['db_key'] = db_key
    formula_data['metadata']['src'] = src
    
    # Сохраняем
    with open(formula_file, 'w', encoding='utf-8') as f:
        json.dump(formula_data, f, ensure_ascii=False, indent=2)
    
    return True


def process_file(file_path: Path, formulas_dir: Path) -> Tuple[int, int]:
    """
    Обрабатывает один markdown файл.
    
    Returns:
        Tuple[int, int]: (количество найденных обёрток, количество обновлённых формул)
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Находим все div-обёртки
    wrappers = find_div_wrappers(content)
    
    if not wrappers:
        return 0, 0
    
    print(f"\n📄 {file_path.relative_to(file_path.parents[1])}")
    print(f"   Найдено обёрток: {len(wrappers)}")
    
    updated_count = 0
    modified_content = content
    
    # Обрабатываем в обратном порядке, чтобы сохранить позиции
    for full_match, db_key, src, formula_id in reversed(wrappers):
        # Обновляем JSON формулы
        if update_formula_json(formula_id, db_key, src, formulas_dir):
            updated_count += 1
            print(f"   ✓ formula_{formula_id}: db_key={db_key}, src={src}")
        
        # Заменяем div-обёртку на просто ссылку
        formula_ref = f"{{{{formula:{formula_id}}}}}"
        modified_content = modified_content.replace(full_match, formula_ref)
    
    # Сохраняем изменённый файл
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(modified_content)
    
    return len(wrappers), updated_count


def copy_directory_structure(source_dir: Path, dest_dir: Path):
    """
    Копирует структуру директории из source в dest.
    """
    if dest_dir.exists():
        print(f"📁 Удаляем существующую директорию: {dest_dir.name}")
        shutil.rmtree(dest_dir)
    
    print(f"📁 Копируем файлы из {source_dir.name} в {dest_dir.name}")
    shutil.copytree(source_dir, dest_dir)


def process_directory(result_dir: Path, formulas_dir: Path) -> Dict[str, int]:
    """
    Обрабатывает все markdown файлы в директории.
    
    Returns:
        Dict со статистикой
    """
    stats = {
        'files_processed': 0,
        'files_with_wrappers': 0,
        'total_wrappers': 0,
        'formulas_updated': 0
    }
    
    # Обходим все markdown файлы
    for md_file in result_dir.rglob('*.md'):
        stats['files_processed'] += 1
        
        wrappers_count, updated_count = process_file(md_file, formulas_dir)
        
        if wrappers_count > 0:
            stats['files_with_wrappers'] += 1
            stats['total_wrappers'] += wrappers_count
            stats['formulas_updated'] += updated_count
    
    return stats


def main():
    """Главная функция."""
    
    # Определяем пути
    script_dir = Path(__file__).parent
    normalized_dir = script_dir.parent
    step03_result_dir = normalized_dir / "step-03-extract-all-illustrations" / "result"
    step04_result_dir = script_dir / "result"
    formulas_dir = normalized_dir / "formulas"
    
    print("=" * 70)
    print("Step 04: Парсинг пропущенных data-db-key и data-src")
    print("=" * 70)
    
    # Проверяем существование директорий
    if not step03_result_dir.exists():
        print(f"❌ Директория не найдена: {step03_result_dir}")
        return
    
    if not formulas_dir.exists():
        print(f"❌ Директория с формулами не найдена: {formulas_dir}")
        return
    
    print(f"\n📂 Исходная директория: step-03-extract-all-illustrations/result")
    print(f"📂 Целевая директория: step-04-parse-missed-db-keys-and-src/result")
    print(f"📂 Директория формул: formulas")
    
    # Копируем файлы из step-03 в step-04
    copy_directory_structure(step03_result_dir, step04_result_dir)
    
    print()
    
    # Обрабатываем все файлы
    stats = process_directory(step04_result_dir, formulas_dir)
    
    # Выводим итоговую статистику
    print("\n" + "=" * 70)
    print("✅ ОБРАБОТКА ЗАВЕРШЕНА")
    print("=" * 70)
    print(f"Обработано файлов: {stats['files_processed']}")
    print(f"Файлов с обёртками: {stats['files_with_wrappers']}")
    print(f"Всего найдено обёрток: {stats['total_wrappers']}")
    print(f"Обновлено формул: {stats['formulas_updated']}")
    
    if stats['total_wrappers'] > stats['formulas_updated']:
        print(f"\n⚠️  Предупреждение: {stats['total_wrappers'] - stats['formulas_updated']} "
              f"обёрток не смогли быть обработаны (файлы формул не найдены)")
    
    # Сохраняем статистику
    stats_file = script_dir / "processing_stats.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 Статистика сохранена: {stats_file.name}")
    print(f"📁 Результаты в: {step04_result_dir.relative_to(normalized_dir)}")


if __name__ == "__main__":
    main()
