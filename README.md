# Web Labs

Лабораторные работы по дисциплине «Веб-программирование».

## Структура

- `lab1/` — лабораторная работа 1: первый HTTP-сервер, Dockerfile, docker-compose, YAML-конфиги (`REPORT.md` — отчёт)
- `lab2/` — лабораторная работа 2: CRUD REST API, OpenAPI-спецификация, проектирование API (`REPORT.md` — отчёт)
- `app/` — код приложения (развивается от лабы к лабе)
- `Dockerfile`, `docker-compose.yml` — контейнеризация текущей версии приложения

## Отчёты

- [Лабораторная работа 1](lab1/REPORT.md) — настройка окружения и первый HTTP-сервер
- [Лабораторная работа 2](lab2/REPORT.md) — REST API для CRUD операций
- [Лабораторная работа 3](lab3/REPORT.md) — валидация и обработка ошибок
- [Лабораторная работа 4](lab4/REPORT.md) — архитектура с разделением слоёв
- [Лабораторная работа 5](lab5/REPORT.md) — тестирование API

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
