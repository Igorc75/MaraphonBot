#!/bin/bash
set -e
docker-compose down
echo "🚀 Запуск MaraphonBot в Docker..."

# Сборка и запуск контейнера
docker-compose up -d --build

# Показываем логи в реальном времени
echo "📄 Логи бота (Ctrl+C для выхода):"
docker-compose logs -f