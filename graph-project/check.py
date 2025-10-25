#!/usr/bin/env python3
"""
Проверка установки и конфигурации graph-project
"""
import sys
from pathlib import Path

def check_python_version():
    """Проверка версии Python"""
    print("🐍 Проверка Python...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ❌ Python {version.major}.{version.minor}.{version.micro} (требуется 3.8+)")
        return False

def check_dependencies():
    """Проверка установленных зависимостей"""
    print("\n📦 Проверка зависимостей...")
    
    required = [
        'neo4j',
        'click',
        'yaml',
        'tqdm',
        'dotenv'
    ]
    
    missing = []
    for module in required:
        try:
            if module == 'yaml':
                __import__('yaml')
            elif module == 'dotenv':
                __import__('dotenv')
            else:
                __import__(module)
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ❌ {module} не установлен")
            missing.append(module)
    
    return len(missing) == 0

def check_config():
    """Проверка конфигурационных файлов"""
    print("\n⚙️  Проверка конфигурации...")
    
    config_file = Path(__file__).parent / "config" / "config.yml"
    env_file = Path(__file__).parent / ".env"
    
    if config_file.exists():
        print(f"  ✓ config.yml найден")
    else:
        print(f"  ⚠️  config.yml не найден (используется config.example.yml)")
    
    if env_file.exists():
        print(f"  ✓ .env найден")
    else:
        print(f"  ⚠️  .env не найден (используется .env.example)")
    
    return True

def check_neo4j_connection():
    """Проверка подключения к Neo4j"""
    print("\n🔌 Проверка подключения к Neo4j...")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.utils.config import load_config
        from src.utils.neo4j_connection import Neo4jConnection
        
        config = load_config()
        conn = Neo4jConnection(
            uri=config['neo4j']['uri'],
            user=config['neo4j']['username'],
            password=config['neo4j']['password'],
            database=config['neo4j']['database']
        )
        
        result = conn.execute_query('RETURN 1 as num')
        if result and result[0]['num'] == 1:
            print(f"  ✓ Подключение к {config['neo4j']['uri']} успешно")
            
            # Получить статистику
            stats = conn.get_stats()
            print(f"\n  Статистика базы данных:")
            for key, value in stats.items():
                if value > 0:
                    print(f"    {key}: {value}")
            
            conn.close()
            return True
        else:
            print(f"  ❌ Неожиданный результат запроса")
            return False
            
    except Exception as e:
        print(f"  ❌ Ошибка подключения: {e}")
        print(f"\n  Убедитесь, что:")
        print(f"    1. Neo4j запущен (neo4j status)")
        print(f"    2. Настройки в config/config.yml корректны")
        print(f"    3. Порты 7474 и 7687 доступны")
        return False

def check_data_sources():
    """Проверка наличия исходных данных"""
    print("\n📁 Проверка исходных данных...")
    
    base_path = Path(__file__).parent.parent
    
    paths_to_check = {
        'formulas': base_path / 'normalized' / 'formulas',
        'symbols': base_path / 'normalized' / 'symbols',
        'illustrations': base_path / 'normalized' / 'illustrations',
        'tables': base_path / 'normalized' / 'tables',
        'literature': base_path / 'normalized' / 'literature',
        'docs': base_path / 'docs',
    }
    
    all_exist = True
    for name, path in paths_to_check.items():
        if path.exists():
            if path.is_dir():
                count = len(list(path.glob('*.json'))) if name != 'docs' else len(list(path.glob('chapter_*')))
                print(f"  ✓ {name}: {count} файлов/директорий")
            else:
                print(f"  ✓ {name}")
        else:
            print(f"  ❌ {name}: не найден по пути {path}")
            all_exist = False
    
    return all_exist

def main():
    """Главная функция проверки"""
    print("\n" + "=" * 70)
    print("ПРОВЕРКА УСТАНОВКИ GRAPH-PROJECT")
    print("=" * 70)
    
    checks = [
        ("Python версия", check_python_version),
        ("Зависимости", check_dependencies),
        ("Конфигурация", check_config),
        ("Исходные данные", check_data_sources),
        ("Neo4j подключение", check_neo4j_connection),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Ошибка при проверке {name}: {e}")
            results.append((name, False))
    
    # Итоговый отчёт
    print("\n" + "=" * 70)
    print("РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("=" * 70)
    
    for name, result in results:
        status = "✓" if result else "❌"
        print(f"  {status} {name}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print("\n✅ Все проверки пройдены! Система готова к работе.")
        print("\nДля начала работы:")
        print("  python main.py import all        # Импортировать данные")
        print("  python main.py stats              # Показать статистику")
        print("  python examples.py                # Запустить примеры")
    else:
        print("\n⚠️  Некоторые проверки не пройдены.")
        print("Следуйте инструкциям выше для устранения проблем.")
    
    print("=" * 70 + "\n")
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
