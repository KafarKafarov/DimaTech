# DimaTech

Асинхронное REST API приложение на `FastAPI`, `SQLAlchemy 2.x`, `PostgreSQL`, `Redis` и `Docker Compose`.

## Что реализовано

- аутентификация пользователя и администратора по `email/password` через JWT
- получение профиля текущего пользователя
- просмотр пользователем своих счетов и платежей
- админский CRUD пользователей
- просмотр администратором списка пользователей вместе со счетами
- обработка платежного вебхука с проверкой `signature`
- идемпотентность по `transaction_id`
- кеширование чтений через Redis с инвалидацией после мутаций
- миграция с тестовыми данными
- `Makefile` с `make lint` и `make test`

## Учетные данные по умолчанию

- пользователь: `user@example.com` / `user12345`
- администратор: `admin@example.com` / `admin12345`

## Быстрый старт через Docker Compose

### Требования

- установленный Docker
- установленный Docker Compose Plugin

### Запуск

```bash
docker compose up --build
```

После старта приложение будет доступно по адресу:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

Миграции применяются автоматически в `entrypoint`.

### Остановка

```bash
docker compose down
```

Для удаления данных PostgreSQL:

```bash
docker compose down -v
```

## Запуск без Docker Compose

### Требования

- Python `3.12+`
- PostgreSQL `16+`
- Redis `7+`

### Подготовка окружения

```bash
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cp .env.example .env
```

Создайте базу данных:

```sql
CREATE DATABASE dimatech;
```

При необходимости скорректируйте параметры подключения в `.env`.

### Миграции

```bash
.venv/bin/alembic upgrade head
```

### Запуск приложения

```bash
.venv/bin/uvicorn main:app --reload
```

Приложение будет доступно по адресу `http://localhost:8000`.

## Полезные команды

```bash
make lint
make test
make migrate
make format
```

## Пример логина

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@example.com",
    "password": "admin12345"
  }'
```

## Пример вебхука

Для секрета `gfdmhghif38yrf9ew0jkf32` валидный пример из задания:

```json
{
  "transaction_id": "5eae174f-7cd0-472c-bd36-35660f00132b",
  "user_id": 1,
  "account_id": 1,
  "amount": 100,
  "signature": "7b47e41efe564a062029da3367bde8844bea0fb049f894687cee5d57f2858bc8"
}
```

Эндпоинт:

```text
POST /api/v1/payments/webhook
```
