#!/bin/bash

echo "========================================"
echo "🚀 Git Update Script для MaraphonBot"
echo "========================================"

# Проверяем, есть ли изменения
if [[ -z $(git status -s) ]]; then
    echo "❌ Нет изменений для коммита"
    exit 0
fi

# Показываем изменения
echo "📋 Текущие изменения:"
git status -s

# Запрашиваем комментарий
echo ""
echo "✏️  Введите описание изменений (или просто нажмите Enter для авто-комментария):"
read commit_message

if [[ -z "$commit_message" ]]; then
    commit_message="Auto update $(date '+%Y-%m-%d %H:%M')"
    echo "⚠️  Использую: $commit_message"
fi

# Добавляем, коммитим, пушим
echo ""
echo "📦 Добавляем файлы..."
git add .

echo "💾 Создаем коммит..."
git commit -m "$commit_message"

echo "📤 Отправляем на GitHub..."
git push origin main

# Показываем результат
echo ""
echo "✅ Готово! Последние коммиты:"
git log --oneline -3