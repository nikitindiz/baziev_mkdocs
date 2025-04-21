#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Функция для печати сообщений с цветом
print_message() {
    echo -e "${GREEN}[DEPLOY]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверяем, установлен ли git
if ! command -v git &> /dev/null; then
    print_error "Git не установлен. Установите его перед продолжением."
    exit 1
fi

# Проверяем, инициализирован ли git репозиторий
if [ ! -d .git ]; then
    print_warning "Git репозиторий не найден. Инициализируем новый репозиторий."
    git init
    git add .
    git commit -m "Initial commit"
fi

# Проверяем наличие виртуального окружения
print_message "Проверка виртуального окружения..."
if [ ! -d "venv" ]; then
    print_message "Создание виртуального окружения..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
print_message "Активация виртуального окружения..."
# Определяем разделитель пути в зависимости от ОС
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Установка зависимостей
print_message "Установка зависимостей..."
pip install -r requirements.txt
pip install mkdocs-gh-deploy

# Убедимся, что все изменения в текущей ветке сохранены
if [ -n "$(git status --porcelain)" ]; then
    print_warning "У вас есть несохраненные изменения в рабочей директории."
    read -p "Хотите продолжить и сохранить изменения? [y/N] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_error "Отмена операции."
        exit 1
    fi
    
    print_message "Сохранение изменений в текущей ветке..."
    git add .
    git commit -m "Сохранение изменений перед деплоем на gh-pages"
fi

# Получаем текущую ветку
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

# Разделение файла на страницы
# print_message "Разделение файла на страницы..."
# python split_book.py

# Деплой на GitHub Pages
print_message "Деплой на GitHub Pages..."
mkdocs gh-deploy --force

# Возвращаемся к исходной ветке
print_message "Возвращаемся к ветке $CURRENT_BRANCH..."
git checkout $CURRENT_BRANCH

print_message "Готово! Ваш сайт успешно опубликован на GitHub Pages."
print_message "Он будет доступен по адресу: https://YOUR-USERNAME.github.io/YOUR-REPO-NAME/"
print_message "Не забудьте заменить YOUR-USERNAME и YOUR-REPO-NAME на ваши данные."
print_message "Для настройки домена, перейдите в настройки репозитория на GitHub > Pages."
