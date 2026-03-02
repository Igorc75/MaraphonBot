# Используем стабильную версию Python 3.12 (полностью совместима со всеми библиотеками)
FROM python:3.12-slim

# Установка локали для корректной работы с кириллицей
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Создание рабочей директории
WORKDIR /app

# Копирование зависимостей и установка
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . .

# Создание файла БД для сохранения данных на хосте
RUN touch maraphon.db && chmod 666 maraphon.db

# Порт для возможного веб-интерфейса (не используется в текущем проекте)
EXPOSE 8000

# Запуск бота
CMD ["python", "bot.py"]