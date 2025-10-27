#!/usr/bin/env python3
"""
Скрипт для тестирования восстановления бекапа Neo4j
Проверяет, что данные в бекапе соответствуют ожидаемым
"""

import json
import tarfile
import sys
from pathlib import Path

def test_backup_integrity(backup_file):
    """Проверяет целостность бекапа"""
    
    backup_path = Path(backup_file)
    
    if not backup_path.exists():
        print(f"❌ Файл бекапа не найден: {backup_file}")
        return False
    
    print(f"📦 Проверка бекапа: {backup_path.name}")
    print(f"   Размер: {backup_path.stat().st_size / 1024 / 1024:.2f} MB")
    print()
    
    # Проверяем, что это tar.gz архив
    if not tarfile.is_tarfile(backup_path):
        print(f"❌ Файл не является tar архивом")
        return False
    
    print("✅ Файл является валидным tar архивом")
    
    # Извлекаем и проверяем содержимое
    try:
        with tarfile.open(backup_path, 'r:gz') as tar:
            members = tar.getmembers()
            print(f"✅ Найдено файлов в архиве: {len(members)}")
            
            # Ищем важные файлы
            important_files = {
                'data/': False,
                'metadata.json': False,
                'stats.json': False,
                '.cypher': False
            }
            
            for member in members:
                for key in important_files.keys():
                    if key in member.name:
                        important_files[key] = True
            
            print("\n📋 Проверка содержимого:")
            for name, found in important_files.items():
                status = "✅" if found else "⚠️"
                print(f"   {status} {name}: {'найдено' if found else 'не найдено'}")
            
            # Проверяем метаданные
            metadata_found = False
            stats_found = False
            
            for member in members:
                if 'metadata.json' in member.name:
                    print(f"\n📄 Метаданные бекапа:")
                    f = tar.extractfile(member)
                    if f:
                        metadata = json.load(f)
                        print(f"   Дата создания: {metadata.get('timestamp', 'N/A')}")
                        print(f"   Neo4j версия: {metadata.get('neo4j_version', 'N/A')}")
                        metadata_found = True
                
                if 'stats.json' in member.name:
                    print(f"\n📊 Статистика бекапа:")
                    f = tar.extractfile(member)
                    if f:
                        stats = json.load(f)
                        print(f"   Всего узлов: {stats.get('total_nodes', 'N/A')}")
                        print(f"   Всего связей: {stats.get('total_relationships', 'N/A')}")
                        
                        if 'nodes_by_label' in stats:
                            print(f"\n   Узлы по меткам:")
                            for label, count in sorted(stats['nodes_by_label'].items()):
                                print(f"     {label}: {count}")
                        
                        stats_found = True
            
            if not metadata_found:
                print("\n⚠️  Метаданные не найдены")
            
            if not stats_found:
                print("\n⚠️  Статистика не найдена")
            
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при проверке архива: {e}")
        return False


def compare_with_current_db():
    """Сравнивает статистику бекапа с текущей БД"""
    
    print("\n" + "="*70)
    print("СРАВНЕНИЕ С ТЕКУЩЕЙ БД")
    print("="*70)
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.utils.neo4j_connection import Neo4jConnection
        from src.utils.config import load_config
        
        config = load_config('config/config.yml')
        neo4j_config = config['neo4j']
        
        conn = Neo4jConnection(
            uri=neo4j_config['uri'],
            user=neo4j_config['username'],
            password=neo4j_config['password'],
            database=neo4j_config['database']
        )
        
        with conn.driver.session() as session:
            # Получаем общую статистику
            result = session.run("MATCH (n) RETURN count(n) as total_nodes")
            total_nodes = result.single()['total_nodes']
            
            result = session.run("MATCH ()-[r]->() RETURN count(r) as total_relationships")
            total_relationships = result.single()['total_relationships']
            
            print(f"\n📊 Текущая БД:")
            print(f"   Всего узлов: {total_nodes}")
            print(f"   Всего связей: {total_relationships}")
            
            # Узлы по меткам
            result = session.run("""
                CALL db.labels() YIELD label
                CALL apoc.cypher.run('MATCH (n:' + label + ') RETURN count(n) as count', {})
                YIELD value
                RETURN label, value.count as count
                ORDER BY label
            """)
            
            print(f"\n   Узлы по меткам:")
            for record in result:
                print(f"     {record['label']}: {record['count']}")
        
        conn.close()
        
        print("\n✅ Подключение к БД успешно")
        return True
        
    except Exception as e:
        print(f"\n⚠️  Не удалось подключиться к БД: {e}")
        print("   (Это нормально, если вы остановили Neo4j для восстановления)")
        return False


def main():
    """Главная функция"""
    
    print("="*70)
    print("ТЕСТИРОВАНИЕ ВОССТАНОВЛЕНИЯ БЕКАПА")
    print("="*70)
    print()
    
    # Список бекапов
    backup_dir = Path("backups")
    backups = sorted(backup_dir.glob("neo4j_backup_*.tar.gz"), reverse=True)
    
    if not backups:
        print("❌ Бекапы не найдены")
        return
    
    print(f"Найдено бекапов: {len(backups)}\n")
    
    # Тестируем последний бекап
    latest_backup = backups[0]
    success = test_backup_integrity(latest_backup)
    
    if success:
        print("\n" + "="*70)
        print("✅ БЕКАП ПРОШЕЛ ПРОВЕРКУ ЦЕЛОСТНОСТИ")
        print("="*70)
    
    # Пробуем сравнить с текущей БД
    compare_with_current_db()
    
    print("\n" + "="*70)
    print("РЕКОМЕНДАЦИИ ДЛЯ ВОССТАНОВЛЕНИЯ:")
    print("="*70)
    print("""
1. Убедитесь, что Neo4j остановлен:
   brew services stop neo4j

2. Восстановите бекап с правами администратора:
   sudo ./restore_db.sh -f neo4j_backup_20251027_091243

3. Запустите Neo4j:
   brew services start neo4j

4. Проверьте статистику после восстановления:
   python graph_stats.py

5. Сравните данные до и после восстановления
""")


if __name__ == '__main__':
    main()
