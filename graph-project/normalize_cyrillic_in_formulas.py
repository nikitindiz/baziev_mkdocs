#!/usr/bin/env python3
"""
Скрипт для нормализации кириллицы в формулах Neo4j.
Заменяет прямую кириллицу на обёрнутую в \\text{}.
"""

import re
from neo4j import GraphDatabase
import os
import yaml

# Загрузка конфигурации
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'config.yml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

config = load_config()

# Подключение к базе данных
NEO4J_URI = config['neo4j']['uri']
NEO4J_USER = config['neo4j']['username']
NEO4J_PASSWORD = config['neo4j']['password']

class CyrillicNormalizer:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
    
    def close(self):
        self.driver.close()
    
    def normalize_cyrillic_text(self, latex_text):
        """
        Заменяет прямые вхождения кириллицы на обёрнутые в \\text{}.
        Примеры:
        - _{ед} -> _{\text{ед}}
        - _{г} -> _{\text{г}}
        - ^{п} -> ^{\text{п}}
        - Дж -> \text{Дж}
        - м -> \text{м}
        - и т.д.
        """
        
        result = latex_text
        
        # Сначала обработаем индексы и степени: _{...} и ^{...}
        def replace_subscript_superscript(match):
            prefix = match.group(1)  # _ или ^
            content = match.group(2)  # содержимое
            
            # Если уже есть \text{} или \textrm{}, не трогаем
            if '\\text{' in content or '\\textrm{' in content:
                return match.group(0)
            
            # Если есть кириллица, оборачиваем
            if re.search(r'[а-яА-ЯёЁ]', content):
                # Если содержимое простое (только кириллица), просто оборачиваем
                if re.match(r'^[а-яА-ЯёЁ]+$', content):
                    return f'{prefix}{{\\text{{{content}}}}}'
                # Если смешанное содержимое, оборачиваем всё
                return f'{prefix}{{\\text{{{content}}}}}'
            
            return match.group(0)
        
        # Обработка _{...} и ^{...}
        result = re.sub(r'([_^])\{([^}]+)\}', replace_subscript_superscript, result)
        
        # Теперь обработаем отдельно стоящую кириллицу
        # Но нужно пропустить кириллицу внутри \text{...}, \textrm{...} и уже обработанных _{...}, ^{...}
        
        # Найдём все позиции, которые находятся внутри \text{...} или \textrm{...}
        protected_ranges = []
        
        # Ищем все вхождения \text{...} и \textrm{...}
        for pattern in [r'\\text\{', r'\\textrm\{']:
            for match in re.finditer(pattern, result):
                start = match.start()
                # Найдём соответствующую закрывающую скобку
                brace_count = 0
                pos = match.end()
                while pos < len(result):
                    if result[pos] == '{':
                        brace_count += 1
                    elif result[pos] == '}':
                        if brace_count == 0:
                            protected_ranges.append((start, pos + 1))
                            break
                        brace_count -= 1
                    pos += 1
        
        def is_protected(start, end):
            """Проверяет, находится ли диапазон внутри защищённой зоны"""
            for pstart, pend in protected_ranges:
                if start >= pstart and end <= pend:
                    return True
            return False
        
        # Найдём все кириллические последовательности и обернём те, что не защищены
        parts = []
        last_end = 0
        
        for match in re.finditer(r'[а-яА-ЯёЁ]+', result):
            start, end = match.span()
            word = match.group(0)
            
            # Пропускаем, если это в защищённой зоне
            if is_protected(start, end):
                parts.append(result[last_end:end])
                last_end = end
                continue
            
            # Пропускаем, если это внутри уже обработанного индекса/степени
            # Проверяем, не стоит ли перед нами открывающая скобка после _ или ^
            if start > 1 and result[start-1] == '{' and result[start-2] in ['_', '^']:
                parts.append(result[last_end:end])
                last_end = end
                continue
            
            # Оборачиваем в \text{}
            parts.append(result[last_end:start])
            parts.append(f'\\text{{{word}}}')
            last_end = end
        
        parts.append(result[last_end:])
        result = ''.join(parts)
        
        return result
    
    def get_formulas_with_cyrillic(self):
        """Получить все формулы с кириллицей, которая не обёрнута в \\text{}."""
        query = """
        MATCH (f:Formula)
        WHERE f.latex =~ '.*[а-яА-ЯёЁ]+.*'
        RETURN f.id AS formula_id, f.latex AS latex
        ORDER BY f.id
        """
        with self.driver.session() as session:
            result = session.run(query)
            return [(record["formula_id"], record["latex"]) for record in result]
    
    def update_formula(self, formula_id, new_latex):
        """Обновить формулу в базе данных."""
        query = """
        MATCH (f:Formula {id: $formula_id})
        SET f.latex = $new_latex
        RETURN f.id AS formula_id
        """
        with self.driver.session() as session:
            result = session.run(query, formula_id=formula_id, new_latex=new_latex)
            return result.single() is not None
    
    def normalize_all_formulas(self, dry_run=True):
        """
        Нормализовать все формулы с кириллицей.
        
        Args:
            dry_run: Если True, только показывает изменения без записи в БД
        """
        formulas = self.get_formulas_with_cyrillic()
        total = len(formulas)
        updated = 0
        unchanged = 0
        
        print(f"Найдено формул с кириллицей: {total}")
        print()
        
        for i, (formula_id, old_latex) in enumerate(formulas, 1):
            # Проверяем, есть ли уже \text{} для всей кириллицы
            if self._is_fully_wrapped(old_latex):
                unchanged += 1
                continue
            
            new_latex = self.normalize_cyrillic_text(old_latex)
            
            if new_latex != old_latex:
                print(f"[{i}/{total}] ID: {formula_id}")
                print(f"  СТАРАЯ: {old_latex}")
                print(f"  НОВАЯ:  {new_latex}")
                print()
                
                if not dry_run:
                    if self.update_formula(formula_id, new_latex):
                        updated += 1
                        print(f"  ✓ Обновлено")
                    else:
                        print(f"  ✗ Ошибка обновления")
                    print()
                else:
                    updated += 1
        
        print(f"\n{'=' * 60}")
        print(f"Всего формул: {total}")
        print(f"Требуют обновления: {updated}")
        print(f"Уже корректные: {unchanged}")
        
        if dry_run:
            print("\n⚠️  DRY RUN - изменения не применены")
            print("Для применения запустите с параметром --apply")
        else:
            print(f"\n✓ Обновлено формул: {updated}")
    
    def _is_fully_wrapped(self, latex):
        """Проверяет, вся ли кириллица уже обёрнута в \\text{}."""
        # Простая эвристика: если нет прямой кириллицы вне \text{}
        # Удаляем все \text{...} и проверяем, осталась ли кириллица
        temp = re.sub(r'\\text\{[^}]*\}', '', latex)
        return not re.search(r'[а-яА-ЯёЁ]', temp)


def main():
    import sys
    
    # Параметры командной строки
    dry_run = '--apply' not in sys.argv
    
    try:
        normalizer = CyrillicNormalizer(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)
        
        print("Нормализация кириллицы в формулах Neo4j")
        print("=" * 60)
        print()
        
        normalizer.normalize_all_formulas(dry_run=dry_run)
        
        normalizer.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
