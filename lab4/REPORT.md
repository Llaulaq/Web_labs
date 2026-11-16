# Лабораторная работа 4: Архитектура приложения с разделением слоёв

**Дисциплина:** Веб-программирование
**Тема:** Устройство backend-приложения

---

## Что сделано

Монолитный обработчик из лабораторной 3 разделён на слои с внедрением зависимостей (DI):

```
HTTP-запрос
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│  API (app/api/users.py)        — обработчики FastAPI      │
│     ↓ зависит от                                          │
│  Service (app/services/users.py) — бизнес-логика          │
│     ↓ зависит от                                          │
│  Repository (app/repositories/users.py) — SQL, sqlite3    │
│     ↓ зависит от                                          │
│  База данных SQLite (путь из конфигурации)                │
└──────────────────────────────────────────────────────────┘
```

- **Конфигурация** (`app/config.py`) читается из переменных окружения: `APP_HOST`, `APP_PORT`, `DATABASE_PATH`, `LOG_LEVEL`; пример — `.env.example`
- **Миграция схемы** (`app/db.py`): `CREATE TABLE IF NOT EXISTS users` с `UNIQUE` на email и `CHECK`-ограничениями
- **Параметризованные запросы** (`?` placeholders) — защита от SQL-инъекций
- **DI через FastAPI Depends** (`get_service` собирает цепочку зависимостей на каждый запрос)
- **Middleware** логирует каждый запрос: метод, путь, статус, время выполнения
- Проверено: вся CRUD-функциональность (201/409/404/204) работает поверх реальной БД; данные переживают перезапуск сервера

## Структура кода

```
app/
├── main.py                  # точка входа, middleware, подключение роутеров
├── config.py                # Settings из переменных окружения
├── db.py                    # подключение SQLite + миграция схемы
├── errors.py                # единый формат ошибок + обработчики
├── schemas.py               # pydantic-модели (UserCreate/UserUpdate/User)
├── api/users.py             # HANDLER: приём HTTP, вызов сервиса
├── services/users.py        # SERVICE: уникальность email, NotFound/Conflict
└── repositories/users.py    # REPOSITORY: только SQL-запросы
```

Проверка через curl (лаба 3) повторена поверх БД — все сценарии проходят.

---

## Задание 1: Разделение ответственности

| Компонент | Ответственность | Класс/методы |
|-----------|-----------------|--------------|
| Handler | Разобрать HTTP-запрос, вызвать сервис, вернуть ответ | `UserController.create(request)` |
| Service | Бизнес-правила: уникальность email, обработка «не найдено» | `UserService.create(data)`, `UserService.get(id)` |
| Repository | SQL-запросы, соединение с БД | `UserRepository.insert(...)`, `UserRepository.find_by_email(...)` |
| Отправка письма | Побочный эффект — выносится в отдельный сервис, вызывается из Service | `EmailService.send_welcome(email)` |

## Задание 2: Dependency Injection

- **UserService** зависит от `UserRepository` и `EmailService` — получает их через конструктор.
- **PostService** зависит от `PostRepository`, `UserRepository` (проверка автора), `TagRepository`.
- **NotificationService** зависит от `EmailService` / шины сообщений.

Схема внедрения: FastAPI `Depends` → фабрика собирает объекты снизу вверх (БД → репозиторий → сервис → обработчик). Компоненты не создают зависимости сами — их легко подменить в тестах.

## Задание 3: Конфигурация через окружение

```python
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_PASSWORD = os.getenv("DB_PASSWORD")          # секрет — без значения по умолчанию
API_KEY = os.getenv("API_KEY")
```

`.env.example` (в репозитории, без секретов) — см. `.env.example`.

**Зачем:** один и тот же артефакт (Docker-образ) работает в dev / test / prod без пересборки; секреты не попадают в код и git; настройки меняются на уровне окружения, а не исходников.

## Задание 4: Побочные эффекты

| Функция | Побочный эффект | Почему |
|---------|:---------------:|--------|
| `add(a, b)` | Нет | Чистая функция, только вычисление |
| `save_user(user)` | **Да** | Меняет состояние БД |
| `send_email(to, subject)` | **Да** | Сеть/SMTP — внешний мир |
| `get_user(user_id)` | Обычно нет* | Только чтение (*если нет кэша/счётчиков) |
| `log(message)` | **Да** | Запись в файл |
| `calculate_total(items)` | Нет | Чистая функция |

Изоляция: побочные эффекты выносятся за интерфейсы (Repository, EmailService), которые внедряются через DI — в тестах подменяются моками, в проде — реальными реализациями.

## Задание 5: Архитектура блога

```
api/posts.py api/comments.py api/tags.py        ← handlers, HTTP
        ↓
services/post_service.py                         ← бизнес-правила:
        ↓                                          пост существует, тег существует,
repositories/                                    автор может комментировать
  post_repository.py comment_repository.py tag_repository.py user_repository.py
        ↓
              PostgreSQL
```

- `POST /posts` → PostService.create(user_id, data) → PostRepository.insert
- `POST /posts/{id}/comments` → CommentService.add(post_id, user_id, text): проверяет пост и пользователя через сервисы → CommentRepository.insert
- `PUT /posts/{id}/tags/{tagId}` → PostService.attach_tag: проверяет существование обеих сущностей → PostRepository.attach_tag

## Задание 6: Рефакторинг create_order

```python
# api/orders.py
@router.post("/orders")
def create_order(request: OrderCreateRequest, service: OrderService = Depends(...)):
    return service.create(request)          # handler тонкий

# services/order_service.py
class OrderService:
    def __init__(self, orders: OrderRepository, products: ProductRepository,
                 users: UserRepository, notifier: NotificationService):
        ...
    def create(self, data) -> Order:
        user = self.users.get(data.user_id) or raise NotFound("User")
        items = [self._reserve(product_id, qty) for product_id, qty in ...]
        order = self.orders.insert(user.id, total(items), items)   # одна транзакция
        self.notifier.order_created(user.email, order)             # побочный эффект
        return order

# repositories/order_repository.py — INSERT заказа и позиций, UPDATE стока
```

Бизнес-логика (подсчёт total, проверка стока) — в Service; побочные эффекты (email) — в NotificationService; работа с БД — в Repository; всё связано через DI.

## Задание 7: Тестирование архитектуры

| Слой | Как тестировать | Что мокать |
|------|-----------------|------------|
| Handler | Integration-тесты через TestClient | Сервис (UserService) |
| Service | Unit-тесты | Репозиторий и внешние сервисы (Email) |
| Repository | Integration-тесты с реальной БД (sqlite/pg в тестах) | Ничего — проверяем реальные SQL-запросы |

При тестировании Handler мокаем Service (проверяем коды/формат ответа); при тестировании Service мокаем Repository (проверяем бизнес-правила без БД); Repository мокать не нужно — его смысл как раз в реальном SQL, тестируем на тестовой БД (это делается в лабораторной 5).

## Задание 8: Практическая реализация

Реализовано в `app/`: тонкие handlers (`app/api/users.py`), сервис с бизнес-правилами (`app/services/users.py`), репозиторий с параметризованным SQL (`app/repositories/users.py`), DI через `Depends` (`get_service`), конфигурация из переменных окружения (`app/config.py`, `.env.example`), middleware логирования запросов, обработка исключений из лабораторной 3. Операции создания/чтения/обновления/удаления проверены через curl поверх SQLite.

---

## Выводы

Приложение перестроено по слоистой архитектуре: каждый слой имеет одну ответственность, зависимости внедряются извне (DI), конфигурация вынесена в переменные окружения, хранилище в памяти заменено на SQLite с миграцией схемы и параметризованными запросами. Архитектура готова к автоматическому тестированию (лабораторная 5).
