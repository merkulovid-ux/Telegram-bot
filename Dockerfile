# AC 1: Используем официальный образ Python
FROM python:3.11-slim

# AC 2: Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app



# AC 3: Копируем requirements.txt и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

# AC 4: Копируем весь остальной код проекта в контейнер
COPY . .

# AC 5: Устанавливаем переменные среды для UTF-8
ENV PYTHONIOENCODING=utf-8
ENV PYTHONUTF8=1

# AC 6: Команда по умолчанию
CMD ["python", "app.py"]

# DoD: Файл соответствует всем AC.