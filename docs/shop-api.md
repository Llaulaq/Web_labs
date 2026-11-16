# API интернет-магазина (Задание 10, занятие 3)

Базовый URL: `https://api.shop.example.com/v1`. Формат данных: JSON. Авторизация: `Authorization: Bearer <token>` (операции, помеченные 🔒).

## Продукты (Products)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/products` | Список: `category`, `min_price`, `max_price`, `search`, `sort`, `page`, `per_page` |
| GET | `/products/{id}` | Один товар |
| POST | `/products` 🔒 | Создание товара |
| PUT | `/products/{id}` 🔒 | Полное обновление |
| PATCH | `/products/{id}` 🔒 | Частичное обновление |
| DELETE | `/products/{id}` 🔒 | Удаление |

## Категории (Categories)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/categories` | Список категорий |
| GET | `/categories/{id}` | Категория |
| GET | `/categories/{id}/products` | Товары категории |
| POST | `/categories` 🔒 | Создание |
| PUT | `/categories/{id}` 🔒 | Обновление |
| DELETE | `/categories/{id}` 🔒 | Удаление |

## Пользователи (Users)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| POST | `/users` | Регистрация |
| GET | `/users/me` 🔒 | Свой профиль |
| PUT | `/users/me` 🔒 | Обновление профиля |
| GET | `/users/{id}` 🔒 | Профиль (админ) |

## Заказы (Orders)

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/orders` 🔒 | Мои заказы (`status`, `date_from`, `date_to`) |
| GET | `/orders/{id}` 🔒 | Заказ (владелец или админ) |
| POST | `/orders` 🔒 | Оформление заказа из корзины |
| PUT | `/orders/{id}/cancel` 🔒 | Отмена заказа |
| GET | `/orders/{id}/items` 🔒 | Элементы заказа |
| POST | `/orders/{id}/items` 🔒 | Добавить позицию (пока заказ не оплачен) |
| DELETE | `/orders/{id}/items/{itemId}` 🔒 | Убрать позицию |

## Пример: оформление заказа

```bash
curl -X POST https://api.shop.example.com/v1/orders \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"items": [{"product_id": 5, "quantity": 2}]}'
```

Ответ `201`:

```json
{
  "id": 1024,
  "user_id": 12,
  "status": "new",
  "total": 5000,
  "items": [{"product_id": 5, "quantity": 2, "price": 2500}],
  "created_at": "2026-11-16T12:00:00Z"
}
```

## Статус-коды

200 — успех, 201 — создано, 204 — удалено, 400 — неверные данные, 401 — не аутентифицирован, 403 — нет прав, 404 — не найдено, 409 — конфликт (например, заказ уже оплачен), 422 — ошибка бизнес-правила.
