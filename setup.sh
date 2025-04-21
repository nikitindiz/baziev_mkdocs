#!/bin/bash

# Создаем виртуальное окружение
echo "Создание виртуального окружения..."
if [ -d "venv" ]; then
    echo "Виртуальное окружение уже существует."
else
    python3 -m venv venv
    echo "Виртуальное окружение создано."
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

# Запуск сервера MkDocs
echo "Запуск сервера MkDocs..."
echo "После запуска сервера перейдите по адресу http://127.0.0.1:8000 в браузере"
mkdocs serve
