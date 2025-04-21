#!/bin/bash

# Создаем виртуальное окружение если его нет
echo "Проверка виртуального окружения..."
if [ -d "venv" ]; then
    echo "Виртуальное окружение уже существует."
else
    echo "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "Активация виртуального окружения..."
# Определяем разделитель пути в зависимости от ОС
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Установка зависимостей
echo "Установка зависимостей..."
pip install mkdocs mkdocs-material pyyaml

# Разделение файла на страницы
echo "Разделение файла на страницы..."
python split_book.py

# Сборка статического сайта
echo "Сборка статического сайта..."
mkdocs build

echo "Готово! Статический сайт создан в директории 'site'."
