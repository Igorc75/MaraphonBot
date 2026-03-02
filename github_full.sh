#!/bin/bash
# github_full.sh - Полная выгрузка проекта на GitHub в ветку main

# --- ОПРЕДЕЛЯЕМ КОРНЕВУЮ ПАПКУ ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Проверяем наличие main.py и .env в корне
if [ ! -f "main.py" ]; then
    echo "❌ main.py не найден в $SCRIPT_DIR"
    exit 1
fi

if [ ! -f ".env" ]; then
    echo "❌ .env не найден в $SCRIPT_DIR"
    exit 1
fi

# Читаем токен
GITHUB_TOKEN=$(grep -E "^GITHUB_TOKEN=" .env | cut -d '=' -f2-)
if [ -z "$GITHUB_TOKEN" ]; then
    echo "❌ GITHUB_TOKEN пустой или не найден"
    exit 1
fi
echo "🔑 GITHUB_TOKEN загружен успешно."

# Читаем название проекта
PROJECT_NAME=$(grep -E "^PROJECT_NAME=" .env | cut -d '=' -f2-)
if [ -z "$PROJECT_NAME" ]; then
    echo "❌ PROJECT_NAME пустой или не найден"
    exit 1
fi
echo "🔑 PROJECT_NAME загружен успешно."

# Читаем имя пользователя GitHub
GITHUB_USER=$(grep -E "^GITHUB_USER=" .env | cut -d '=' -f2-)
if [ -z "$GITHUB_USER" ]; then
    echo "❌ GITHUB_USER пустой или не найден"
    exit 1
fi
echo "🔑 GITHUB_USER загружен успешно: $GITHUB_USER"

echo "🚀 Подготовка выгрузки в ветку main..."

TMP_DIR=$(mktemp -d)
echo "📁 Временная папка: $TMP_DIR"

# --- ФУНКЦИЯ ДЛЯ ЧТЕНИЯ .GITIGNORE ---
create_exclude_file() {
    local exclude_file="$1"
    
    echo "# Автоматически сгенерированные исключения из .gitignore" > "$exclude_file"
    
    # Обязательные исключения (включая .git)
    echo ".env" >> "$exclude_file"
    echo "*.db" >> "$exclude_file"
    echo "*.sqlite" >> "$exclude_file"
    echo "*.db-journal" >> "$exclude_file"
    echo ".git" >> "$exclude_file"
    echo "/.git" >> "$exclude_file"
    
    # Читаем .gitignore если он существует
    if [ -f ".gitignore" ]; then
        echo "# --- Исключения из .gitignore ---" >> "$exclude_file"
        while IFS= read -r line || [ -n "$line" ]; do
            if [[ -z "$line" || "$line" =~ ^[[:space:]]*$ || "$line" =~ ^# ]]; then
                continue
            fi
            line=$(echo "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')
            if [[ "$line" =~ ^! ]]; then
                continue
            fi
            echo "$line" >> "$exclude_file"
        done < ".gitignore"
    else
        echo "⚠️  .gitignore не найден, используются только базовые исключения"
    fi
    
    # Дополнительные исключения
    echo "# --- Дополнительные исключения ---" >> "$exclude_file"
    echo "/venv" >> "$exclude_file"
    echo "/.venv" >> "$exclude_file"
    echo "/env" >> "$exclude_file"
    echo "__pycache__" >> "$exclude_file"
    echo ".DS_Store" >> "$exclude_file"
    echo "Thumbs.db" >> "$exclude_file"
    echo "desktop.ini" >> "$exclude_file"
    echo ".pytest_cache" >> "$exclude_file"
    echo ".vscode" >> "$exclude_file"
    echo ".idea" >> "$exclude_file"
    echo "*.code-workspace" >> "$exclude_file"
    echo ".mypy_cache" >> "$exclude_file"
    echo ".ruff_cache" >> "$exclude_file"
    echo "*.pyc" >> "$exclude_file"
    echo "*.pyo" >> "$exclude_file"
    echo "*.pyd" >> "$exclude_file"
    echo ".Python" >> "$exclude_file"
    echo "pip-log.txt" >> "$exclude_file"
    echo "*.egg-info" >> "$exclude_file"
    echo ".eggs" >> "$exclude_file"
    echo ".tox" >> "$exclude_file"
    echo "coverage.xml" >> "$exclude_file"
    echo ".coverage" >> "$exclude_file"
    echo ".coverage.*" >> "$exclude_file"
    echo "htmlcov" >> "$exclude_file"
    echo "*.orig" >> "$exclude_file"
    echo "*.rej" >> "$exclude_file"
    echo "*.bak" >> "$exclude_file"
    echo "*.swp" >> "$exclude_file"
    echo "*.swo" >> "$exclude_file"
    echo "*~" >> "$exclude_file"
    echo ".*.swp" >> "$exclude_file"
    echo ".*.swo" >> "$exclude_file"
    echo "session.sql" >> "$exclude_file"
    echo "config.local.*" >> "$exclude_file"
    echo "secrets.*" >> "$exclude_file"
    echo "private.*" >> "$exclude_file"
    echo "test.db" >> "$exclude_file"
    echo "instance" >> "$exclude_file"
    echo "migrations" >> "$exclude_file"
    echo ".gitignore_global" >> "$exclude_file"
    echo ".gitattributes" >> "$exclude_file"
    echo ".editorconfig" >> "$exclude_file"
    echo "logs" >> "$exclude_file"
    echo "*.csv" >> "$exclude_file"
    echo "*.xlsx" >> "$exclude_file"
    echo "*.xls" >> "$exclude_file"
    echo "uploads" >> "$exclude_file"
    echo "media" >> "$exclude_file"
    echo "static" >> "$exclude_file"
    echo "assets" >> "$exclude_file"
    echo "images" >> "$exclude_file"
    echo "*.jpg" >> "$exclude_file"
    echo "*.jpeg" >> "$exclude_file"
    echo "*.png" >> "$exclude_file"
    echo "*.gif" >> "$exclude_file"
    echo "*.mp4" >> "$exclude_file"
    echo "*.mp3" >> "$exclude_file"
    echo "*.wav" >> "$exclude_file"
    echo "*.zip" >> "$exclude_file"
    echo "*.tar.gz" >> "$exclude_file"
    echo "*.rar" >> "$exclude_file"
    echo "temp" >> "$exclude_file"
    echo "tmp" >> "$exclude_file"
    echo "cache" >> "$exclude_file"
    echo ".cache" >> "$exclude_file"
    
    echo "✅ Файл исключений создан: $exclude_file"
}

# Создаем временный файл с исключениями
EXCLUDE_FILE=$(mktemp)
create_exclude_file "$EXCLUDE_FILE"
echo "venv*" >> "$EXCLUDE_FILE"

# Показываем содержимое файла исключений (для отладки)
if [ "${DEBUG:-false}" = "true" ]; then
    echo "📋 Содержимое файла исключений:"
    cat "$EXCLUDE_FILE"
    echo ""
fi

# Копируем проект во временную директорию с исключениями
echo "📁 Копируем файлы с исключениями из .gitignore..."
rsync -av --exclude-from="$EXCLUDE_FILE" ./ "$TMP_DIR/project/"

# Удаляем временный файл исключений
rm "$EXCLUDE_FILE"

cd "$TMP_DIR/project"

# Инициализируем git и создаем коммит
git init >/dev/null
git checkout -b main >/dev/null

git config user.name "igorc75"
git config user.email "ic75@mail.ru"

git add .
git commit -m "Обновление $(date '+%d.%m.%Y %H:%M')" >/dev/null

echo "📤 Отправка на GitHub в ветку main (с перезаписью)..."
git push --force "https://$GITHUB_TOKEN@github.com/$GITHUB_USER/$PROJECT_NAME.git" main >/dev/null

# Проверяем результат
echo "🔍 Проверяем наличие обновлений на GitHub..."

sleep 5

MAX_ATTEMPTS=3
for ((i=1; i<=MAX_ATTEMPTS; i++)); do
    BRANCH_CHECK=$(curl -s "https://api.github.com/repos/$GITHUB_USER/$PROJECT_NAME/branches/main" | grep '"name"')
    if [[ -n "$BRANCH_CHECK" ]]; then
        echo ""
        echo "✅ УСПЕХ! Проект обновлен в ветке main."
        echo "🔗 https://github.com/$GITHUB_USER/$PROJECT_NAME/tree/main"
        exit 0
    fi
    echo "   Попытка $i/$MAX_ATTEMPTS: проверяем..."
    sleep 5
done

echo ""
echo "❌ ОШИБКА: Не удалось проверить обновление на GitHub!"
exit 1