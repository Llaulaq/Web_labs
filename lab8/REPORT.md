# Лабораторная работа 8: Nginx reverse proxy и безопасность

**Дисциплина:** Веб-программирование
**Тема:** Веб-сервер (Nginx) + Безопасность веб-приложения

---

## Что сделано

### Nginx (`lab8/nginx/nginx.conf`)

- **Reverse proxy**: `/` → `http://app:8000` с заголовками `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`
- **Статика**: `location /static/` отдаётся Nginx напрямую (`alias`), с кэшированием `expires 30d`
- **HTTPS**: сервер на 443 с TLS 1.2/1.3, самоподписанный сертификат (`lab8/nginx/generate-certs.sh`), редирект 80 → 443, HSTS
- **Заголовки безопасности**: `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Content-Security-Policy: default-src 'self'`
- **Rate limiting**: `limit_req_zone` 5 r/s на IP с burst=10 — защита от брутфорса `/auth/login`
- **gzip** для text/json/css/js
- **Docker-стек** (`lab8/docker-compose.yml`): app + nginx (порты 80/443)

Запуск (требуется Docker):

```bash
bash lab8/nginx/generate-certs.sh
docker compose -f lab8/docker-compose.yml up --build
# https://localhost — API через прокси; https://localhost/static/ — статика
```

### Безопасность приложения

- **SQL-инъекции**: все запросы параметризованы (`?` placeholders) — демонстрация в `lab8/sql_injection_demo.py`
- **Пароли**: PBKDF2-HMAC-SHA256 + соль (лаба 6), сравнение `hmac.compare_digest`
- **Авторизация**: JWT + проверка типа токена + blacklist (лаба 6); 401 на всё без токена
- **CORS** (`app/main.py`): `CORSMiddleware`, список origin'ов из `ALLOWED_ORIGINS` (env), ограниченные методы и заголовки, без wildcard `*`
- **Утечки**: пароль исключён из всех ответов (`exclude=True`), секреты только из env, в логах токенов и паролей нет

## Демонстрация SQL-инъекции (lab8/sql_injection_demo.py)

```
=== 1. Обход авторизации: ' OR '1'='1 ===
  SQL: SELECT * FROM users WHERE email = '' OR '1'='1'
уязвимый вариант:   вход РАЗРЕШЁН
  SQL: SELECT * FROM users WHERE email = ?  параметры: ("' OR '1'='1",)
защищённый вариант: вход запрещён

=== 2. Чужой аккаунт: admin@example.com'-- ===
  SQL: SELECT * FROM users WHERE email = 'admin@example.com'--'
уязвимый вариант:   вход РАЗРЕШЁН
защищённый вариант: вход запрещён
```

Вся разница — в передаче email как параметра вместо подстановки в строку запроса.

## Проверка в Docker (выполнено)

```bash
bash lab8/nginx/generate-certs.sh                      # самоподписанный сертификат
docker compose -f lab8/docker-compose.yml up -d --build
```

Результаты проверки:

```
GET  http://localhost/health      → 301 → https://localhost/health   (редирект 80→443)
GET  https://localhost/health     → 200 {"status":"ok"}              (API через прокси)
GET  https://localhost/static/css/style.css → 200                    (статика напрямую nginx)
POST https://localhost/auth/register → 201                           (запись в БД в volume)
POST https://localhost/auth/login → access+refresh токены
GET  https://localhost/auth/me + Bearer → 200 профиль

Заголовки ответа:
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Strict-Transport-Security: max-age=31536000
  Content-Security-Policy: default-src 'self'

Rate limiting (20 быстрых запросов к /health):
  200 x12 → 503, 200, 503 x3 …   (лимит 5 r/s, burst=10 — срабатывает)
```

Стоп: `docker compose -f lab8/docker-compose.yml down`. Сертификаты (`lab8/nginx/certs/`) в репозиторий не коммитятся — генерируются скриптом.

## Ответы на задания занятия 11

### Задание 1: Хеширование паролей

Реализовано в `app/security.py`: PBKdf2 (100 000 итераций) с уникальной солью на пароль; хранится `pbkdf2$<salt>$<hash>`. Сравнение с «открытым» хранением: при утечке БД злоумышленник получает все пароли сразу; с солью+хешем подбор каждого пароля — отдельный перебор, замедленный итерациями. bcrypt — тот же класс решений (адаптивный хеш, соль встроена), выбран PBKDF2 из stdlib без внешних зависимостей.

### Задание 2: SQL Injection

См. демонстрацию выше. Атаки: `' OR '1'='1` (обход логина), `admin'--` (комментарий отрезает проверку пароля), `'; DROP TABLE users;--` (разрушение данных). Защита: параметризованные запросы (в проекте — везде), минимальные права учётки БД (нет DDL), ORM как дополнительный слой.

### Задание 3: XSS

Типы: хранимая (комментарий с `<script>` читают другие), отражённая (параметр URL вставляется в страницу), DOM-based (JS читает location и вставляет в DOM). Защита в проекте: CSP `default-src 'self'` (запрет inline-скриптов), `X-Content-Type-Options: nosniff`; для вывода пользовательского контента — экранирование (FastAPI экранирует в шаблонах; JSON API не рендерит HTML); токены в Authorization-заголовке, а не cookie → кража через XSS не даёт CSRF-возможностей автоматически.

### Задание 4: CSRF

Атака: чужой сайт отправляет форму от имени авторизованного пользователя (cookie отправляются автоматически). Защита в проекте: JWT в заголовке `Authorization` — браузер не добавляет его кросс-сайтово (CSRF неприменим); CORS-политика ограничивает чтение ответов чужим origin'ам; для cookie-схем добавляются `SameSite=Lax/Strict` + CSRF-токены + проверка Origin.

### Задание 5 (заголовки), 6 (HTTPS), 7 (rate limiting), 8 (проверка прав)

- **Заголовки**: см. nginx.conf — nosniff, DENY frame, CSP, HSTS, Referrer-Policy.
- **HTTPS**: TLS 1.2/1.3, редирект 80→443, HSTS заставляет браузер ходить только по HTTPS; в проде — Let's Encrypt.
- **Rate limiting**: 5 r/s на IP; защищает login от брутфорса и API от сканирования.
- **Проверка прав**: `get_current_user` валидирует токен на каждый запрос; владение ресурсом проверяется по `sub` токена; админ-роли — следующий шаг (claim `role` в JWT).

## Чек-лист безопасности

- [x] Пароли хешированы с солью
- [x] Параметризованные SQL-запросы
- [x] JWT + тип токена + blacklist
- [x] CORS с whitelist origin'ов
- [x] CSP, nosniff, X-Frame-Options, HSTS
- [x] HTTPS с редиректом и современными протоколами
- [x] Rate limiting
- [x] Секреты в env (.env.example без значений)
- [x] Пароль и токены не логируются и не возвращаются
- [ ] Админ-роли и проверка владения ресурсом (после лабы 8)

---

## Выводы

Подготовлена и **проверена в Docker** production-конфигурация Nginx: reverse proxy, раздача статики, HTTPS с редиректом, заголовки безопасности, rate limiting. Приложение защищено от основных уязвимостей OWASP Top 10: инъекции (параметризация), слабые пароли (хеширование), нарушенный контроль доступа (JWT + проверка), XSS (CSP, экранирование), CSRF (токены в заголовке + CORS). Полный стек `app + nginx` поднят и прогнан через curl: все сценарии работают.
