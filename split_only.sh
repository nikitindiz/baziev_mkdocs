#!/bin/bash

# Проверяем наличие виртуального окружения
echo "Проверка виртуального окружения..."
if [ -d "venv" ]; then
    echo "Виртуальное окружение найдено."
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

# Проверяем наличие необходимых зависимостей
if ! pip show pyyaml &> /dev/null; then
    echo "Установка pyyaml..."
    pip install pyyaml
fi

# Разделение файла на страницы
echo "Разделение файла на страницы..."
python split_book.py

echo "Готово! Файл разделен на страницы."
echo "Для запуска локального сервера выполните команду: source venv/bin/activate && mkdocs serve"
echo "Для сборки статического сайта выполните команду: source venv/bin/activate && mkdocs build"
