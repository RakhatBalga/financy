# Деплой (24/7)

Бот работает в режиме **long-polling** — публичный домен, webhook и nginx не
нужны. Нужен только сервер (VPS) с Docker, где стек крутится постоянно.

## Что понадобится
- VPS с Linux (Ubuntu 22.04+), 1 vCPU / 1 GB RAM достаточно.
- Docker + Docker Compose.
- Токен бота (BotFather) и ключ Gemini.

## 1. Установить Docker (если ещё нет)
```bash
curl -fsSL https://get.docker.com | sh
sudo systemctl enable --now docker      # автозапуск после перезагрузки
```

## 2. Забрать код
```bash
git clone https://github.com/RakhatBalga/fincancy.git
cd fincancy
```

## 3. Создать .env
```bash
cp .env.example .env
nano .env
```
Заполнить (остальное можно оставить по умолчанию):
```
BOT_TOKEN=<токен от BotFather>
GEMINI_API_KEY=<ключ Gemini>
GEMINI_MODEL=gemini-2.5-flash
WEBHOOK_URL=            # пусто → polling
POSTGRES_HOST=postgres
REDIS_HOST=redis
TZ=Asia/Almaty
```

## 4. Запустить
```bash
docker compose up -d --build
```
Поднимутся `postgres`, `redis`, `bot-app` (nginx не стартует — он под профилем
`webhook`). Миграции применяются автоматически при старте.

Проверить:
```bash
docker compose logs -f bot-app     # должно быть "Run polling for bot @..."
```

## Обsluживание
```bash
docker compose ps                  # статус
docker compose logs -f bot-app     # логи
git pull && docker compose up -d --build   # обновить до свежей версии
docker compose down                # остановить
docker compose down -v             # остановить и стереть БД (осторожно)
```

## Автоперезапуск
Все сервисы объявлены с `restart: unless-stopped`, а демон Docker включён в
автозагрузку (`systemctl enable docker`) — после перезагрузки сервера бот
поднимется сам. Ничего дополнительно настраивать не нужно.

## Одновременный запуск с другими проектами
Так как в polling-режиме бот не занимает ни один внешний порт (нет проброса
`ports:`), он спокойно живёт на сервере рядом с другими Docker-проектами.
Имена томов/сети префиксуются именем папки (`fincancy_*`), поэтому конфликтов с
чужими контейнерами нет.

## Webhook-режим (опционально, не обязателен)
Нужен домен с HTTPS. Тогда: задать `WEBHOOK_URL=https://твой-домен` в `.env`,
настроить TLS в `nginx/nginx.conf` и запустить с профилем:
```bash
docker compose --profile webhook up -d --build
```
Для личного бота это избыточно — polling полностью достаточно.
