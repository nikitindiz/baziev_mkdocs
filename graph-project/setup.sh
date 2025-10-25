#!/bin/bash

# Установочный скрипт для graph-project

echo "=== Установка Graph Project - Физика Базиева ==="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.8 или новее."
    exit 1
fi

echo "✓ Python найден: $(python3 --version)"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активация виртуального окружения
source venv/bin/activate

# Установка зависимостей
echo "📦 Установка зависимостей..."
pip install --upgrade pip
pip install -r requirements.txt

# Копирование конфигурационных файлов
if [ ! -f "config/config.yml" ]; then
    echo "📝 Создание конфигурационного файла..."
    cp config/config.example.yml config/config.yml
fi

if [ ! -f ".env" ]; then
    echo "📝 Создание .env файла..."
    cp .env.example .env
fi

# Проверка Neo4j
echo ""
echo "=== Проверка Neo4j ==="
echo "Для работы graph-project требуется Neo4j."
echo ""
echo "Установка Neo4j:"
echo "  • MacOS:    brew install neo4j"
echo "  • Docker:   docker run -d --name neo4j-baziev -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest"
echo ""
echo "После установки Neo4j:"
echo "  1. Запустите Neo4j"
echo "  2. Откройте http://localhost:7474"
echo "  3. Настройте пароль (по умолчанию: neo4j/neo4j)"
echo "  4. Обновите config/config.yml с вашими настройками"
echo ""

# Проверка подключения к Neo4j
echo "=== Тестирование подключения к Neo4j ==="
python3 -c "
from src.utils.config import load_config
from src.utils.neo4j_connection import Neo4jConnection
try:
    config = load_config()
    conn = Neo4jConnection(
        uri=config['neo4j']['uri'],
        user=config['neo4j']['username'],
        password=config['neo4j']['password'],
        database=config['neo4j']['database']
    )
    result = conn.execute_query('RETURN 1 as num')
    print('✓ Подключение к Neo4j успешно!')
    conn.close()
except Exception as e:
    print(f'❌ Ошибка подключения к Neo4j: {e}')
    print('Проверьте настройки в config/config.yml и убедитесь, что Neo4j запущен.')
" 2>/dev/null || echo "⚠️  Не удалось подключиться к Neo4j. Настройте подключение в config/config.yml"

echo ""
echo "=== Установка завершена! ==="
echo ""
echo "Использование:"
echo "  source venv/bin/activate           # Активировать окружение"
echo "  python main.py import --all        # Импортировать все данные"
echo "  python main.py query chapter-stats # Показать статистику по главам"
echo "  python main.py stats               # Показать общую статистику"
echo ""
