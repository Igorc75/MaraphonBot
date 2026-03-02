# Makefile для MaraphonBot

.PHONY: run install clean test export github gitignore help

# Запуск бота
run:
	@echo "Активация виртуального окружения и запуск бота..."
	. venv/bin/activate && python3 main.py

# Установка зависимостей
install:
	@echo "Установка зависимостей..."
	python3 -m venv venv
	. venv/bin/activate && pip install --upgrade pip
	. venv/bin/activate && pip install -r requirements.txt
	@echo "✅ Зависимости установлены"

# Очистка кешей и временных файлов
clean:
	@echo "Очистка временных файлов..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.log" -delete
	find . -type f -name "*.csv" -delete
	find . -type f -name "*.db" -delete
	@echo "✅ Очистка завершена"

# Тестирование
test:
	@echo "Запуск тестов..."
	. venv/bin/activate && python -m pytest tests/ -v

# Экспорт кода
export:
	@echo "Экспорт кода в файл..."
	. venv/bin/activate && python export_code.py
	@echo "✅ Код экспортирован в code_export.txt"

# Выгрузка на GitHub
github:
	@echo "Выгрузка на GitHub..."
	bash github_full.sh

# Генерация .gitignore
gitignore:
	@echo "Генерация/обновление .gitignore..."
	bash generate_gitignore.sh

# Создание базы данных
init-db:
	@echo "Инициализация базы данных..."
	. venv/bin/activate && python create_admin_table.py

# Проверка зависимостей
check-deps:
	@echo "Проверка зависимостей..."
	. venv/bin/activate && pip list --outdated

# Форматирование кода
format:
	@echo "Форматирование кода..."
	. venv/bin/activate && python -m black .
	. venv/bin/activate && python -m isort .
	. venv/bin/activate && python -m ruff --fix .

# Проверка типов
type-check:
	@echo "Проверка типов..."
	. venv/bin/activate && python -m mypy .

# Запуск с отладкой
debug:
	@echo "Запуск в режиме отладки..."
	export LOG_LEVEL=DEBUG && . venv/bin/activate && python3 main.py

# Вывод содержимого .gitignore
show-gitignore:
	@echo "Содержимое .gitignore:"
	@cat .gitignore | head -30

# Тест исключений
test-excludes:
	@echo "Тестирование исключений..."
	DEBUG=true bash github_full.sh

# Помощь
help:
	@echo "Доступные команды:"
	@echo "  make run            - Запустить бота"
	@echo "  make install        - Установить зависимости"
	@echo "  make clean          - Очистить временные файлы"
	@echo "  make test           - Запустить тесты"
	@echo "  make export         - Экспортировать код в файл"
	@echo "  make github         - Выгрузить на GitHub"
	@echo "  make gitignore      - Сгенерировать/обновить .gitignore"
	@echo "  make init-db        - Инициализировать базу данных"
	@echo "  make format         - Отформатировать код"
	@echo "  make type-check     - Проверить типы"
	@echo "  make debug          - Запустить с отладкой"
	@echo "  make show-gitignore - Показать содержимое .gitignore"
	@echo "  make test-excludes  - Тестирование исключений (DEBUG)"
	@echo "  make help           - Показать эту справку"