# Telegram Finance Bot

Учёт личных финансов в Telegram: пишешь трату свободным текстом
(`кофе 800`, `такси 1500`, `зарплата 400000`) — бот распознаёт сумму,
категорию и тип через **Gemini** (structured output), сохраняет и показывает
отчёты за день / неделю / месяц. Плюс месячные бюджеты по категориям с
предупреждениями и еженедельный дайджест.

## Стек

- Python 3.12, **aiogram 3.x**, **FastAPI** (webhook)
- PostgreSQL + **SQLAlchemy 2.0 (async)** + Alembic
- Redis (FSM storage), **APScheduler** (фоновые задачи)
- Docker + docker-compose, Nginx (reverse proxy для webhook)
- Gemini API (`google-genai`) — парсинг трат через controlled generation
- structlog — структурированное логирование

Архитектура слоями: `handlers (bot) → services → repositories → models`.
Все обращения к БД и Gemini — асинхронные.

## Структура проекта

```
telegram-finance-bot/
├── app/
│   ├── main.py                     # entrypoint: webhook (FastAPI) или polling
│   ├── core/
│   │   ├── config.py               # Pydantic Settings (.env)
│   │   └── logging.py              # structlog
│   ├── db/
│   │   ├── base.py                 # async engine, session factory, Base
│   │   └── models.py               # User, Category, Transaction, Budget
│   ├── repositories/               # доступ к БД (async), по одной сущности
│   │   ├── user_repo.py
│   │   ├── category_repo.py
│   │   ├── transaction_repo.py
│   │   └── budget_repo.py
│   ├── services/                   # бизнес-логика (use-cases)
│   │   ├── schemas.py              # DTO + схема для Gemini
│   │   ├── periods.py              # границы периодов (сегодня/неделя/месяц)
│   │   ├── parser_service.py       # Gemini structured output
│   │   ├── user_service.py
│   │   ├── transaction_service.py
│   │   ├── analytics_service.py    # чистая агрегация, без AI при чтении
│   │   └── budget_service.py
│   ├── bot/
│   │   ├── dispatcher.py           # Bot + Dispatcher, middleware, DI
│   │   ├── keyboards.py            # inline-клавиатуры + callback-схема
│   │   ├── formatters.py           # рендер отчётов/уведомлений
│   │   ├── middlewares/db.py       # сессия БД на каждый апдейт
│   │   └── handlers/
│   │       ├── start.py            # /start
│   │       ├── reports.py          # /today, /week, /month
│   │       ├── budget.py           # /setbudget
│   │       └── transactions.py     # свободный текст + inline-подтверждение
│   └── scheduler/
│       ├── scheduler.py            # регистрация задач APScheduler
│       └── jobs.py                 # проверка бюджета + недельный дайджест
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/0001_initial.py
├── tests/
│   ├── conftest.py                 # in-memory SQLite + фикстуры
│   ├── test_transaction_service.py
│   └── test_analytics_service.py
├── nginx/nginx.conf
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
└── .env.example
```

## Модель данных

| Таблица        | Поля |
|----------------|------|
| `users`        | id, telegram_id (uniq), username, currency, created_at |
| `categories`   | id, user_id, name, is_default — uniq(user_id, name) |
| `transactions` | id, user_id, category_id, amount, type (expense/income), description, created_at |
| `budgets`      | id, user_id, category_id, monthly_limit, month (`YYYY-MM`) — uniq(user_id, category_id, month) |

## Функциональность

- `/start` — регистрация по `telegram_id` + создание дефолтных категорий
  (Еда, Транспорт, Жильё, Развлечения, Здоровье, Другое).
- Любой текст → парсинг через Gemini → сохранение → inline-кнопки
  «Подтвердить / Изменить категорию».
- `/today`, `/week`, `/month` — сумма трат + разбивка по категориям
  (сумма и % от общего) текстовой таблицей.
- `/setbudget <категория> <сумма>` — месячный лимит по категории.
- Ежедневно 20:00 — проверка бюджетов (>80% и >100%), предупреждения в личку.
- Воскресенье 19:00 — недельный дайджест: топ категорий + сравнение
  с прошлой неделей (% изменения).

## Запуск через Docker

```bash
cp .env.example .env
# впиши BOT_TOKEN и GEMINI_API_KEY в .env (реальный ключ только здесь!)
docker compose up --build
```

Контейнер `bot-app` при старте сам применяет миграции (`alembic upgrade head`),
затем запускается. Если `WEBHOOK_URL` пуст — режим long-polling (для локальной
разработки Nginx не нужен). Задай `WEBHOOK_URL=https://your-domain` для
production через Nginx.

## Локальный запуск без Docker

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # заполни BOT_TOKEN, GEMINI_API_KEY,
                                # POSTGRES_HOST=localhost, REDIS_HOST=localhost
alembic upgrade head
python -m app.main              # WEBHOOK_URL пуст → polling
```

## Тесты

```bash
pip install -r requirements.txt
pytest
```

Тесты `transaction_service` и `analytics_service` работают на in-memory SQLite,
Gemini и Postgres не требуются.

## Как устроен парсинг трат (Gemini)

Вместо «tool use» у Claude используется идиоматичный для Gemini механизм —
**controlled generation**: модели передаётся `response_schema` (Pydantic-класс
`ParsedTransaction`) и `response_mime_type="application/json"`, поэтому ответ
гарантированно валидный JSON нужной формы. См. `app/services/parser_service.py`.

Строгая JSON-схема:

```python
class ParsedTransaction(BaseModel):
    amount: float          # положительная сумма, напр. 800.0
    category: str          # наиболее подходящая категория
    type: TransactionType  # "expense" | "income"
    description: str       # краткое описание
```

Вызов:

```python
response = await client.aio.models.generate_content(
    model="gemini-3.1-pro-preview",
    contents="такси 1500",
    config=types.GenerateContentConfig(
        system_instruction=_SYSTEM_INSTRUCTION,  # правила извлечения (в parser_service.py)
        response_mime_type="application/json",
        response_schema=ParsedTransaction,
        temperature=0.0,
    ),
)
parsed = response.parsed  # -> ParsedTransaction(amount=1500.0, category="Транспорт", ...)
```

Системная инструкция описывает извлечение полей и выбор из стандартных
категорий (иначе «Другое»); доходы (зарплата, перевод, кэшбэк) → `income`.

## Безопасность

- `.env` в `.gitignore` — реальные `BOT_TOKEN` / `GEMINI_API_KEY` в git не
  попадают. Никогда не коммить настоящие ключи.
- Webhook защищён `WEBHOOK_SECRET` (проверка заголовка
  `X-Telegram-Bot-Api-Secret-Token`).
```
