# Web Labs

Лабораторные работы по дисциплине «Веб-программирование».

## Структура

- `app/` — исходный код приложения (FastAPI)
- `docs/` — отчёты по лабораторным работам
- `Dockerfile`, `docker-compose.yml` — контейнеризация приложения
- `docker/` — дополнительные конфигурации

## Отчёты

- [Лабораторная работа 1](docs/lab1.md) — настройка окружения и первый HTTP-сервер

## Запуск

```bash
# Локально (Windows)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Docker
docker compose up --build
```

Открыть http://localhost:8000/docs — интерактивная документация API (Swagger UI).
