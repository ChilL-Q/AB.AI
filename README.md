# AB AI

SaaS-платформа для автосервисов. Удержание клиентов, управление коммуникациями и возврат пропавших клиентов через AI-агентов в WhatsApp и Telegram.

## Стек

| Слой | Технологии |
|------|-----------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, Celery + Redis |
| Frontend | Next.js 15 App Router, TypeScript, Tailwind CSS, shadcn/ui |
| Mobile | React Native (Expo SDK 52), TypeScript, Expo Router |
| DB | PostgreSQL 16, Redis 7 |
| AI | Claude API (Anthropic) |
| Messaging | WhatsApp Business Cloud API, Telegram Bot API |

## Структура репозитория

```
ab-ai/
├── backend/          # FastAPI приложение
├── frontend-web/     # Next.js веб-приложение
├── mobile/           # React Native (Expo) мобильное приложение
├── shared/           # Общие TypeScript типы
└── docker-compose.yml
```

## Быстрый старт (локально)

```bash
# 1. Скопировать env
cp .env.example .env

# 2. Поднять зависимости (Postgres + Redis)
docker compose up postgres redis -d

# 3. Применить миграции
cd backend
python -m alembic upgrade head

# 4. Запустить бэкенд
uvicorn app.main:app --reload

# 5. Запустить фронтенд (в другом терминале)
cd frontend-web
npm install && npm run dev
```

Или всё через Docker:

```bash
cp .env.example .env
docker compose up --build
```

API доступен на `http://localhost:8000`  
Swagger UI: `http://localhost:8000/docs`

## Разработка

```bash
# Backend — форматирование и линтинг
cd backend
ruff check . --fix
ruff format .

# Backend — тесты
pytest

# Frontend — линтинг
cd frontend-web
npm run lint
```

## Модули

1. Аутентификация и управление аккаунтами
2. CRM клиентов и автомобилей
3. Импорт данных (CSV, Excel, 1С, StoCRM)
4. Кампании и триггеры
5. AI-агент для диалогов (Claude API)
6. Шаблоны сообщений
7. Аналитика и ROI
8. Мультиканальность (WhatsApp, Telegram, SMS)
9. Биллинг и подписки
10. Мобильное приложение
11. Уведомления
12. Настройки автосервиса
