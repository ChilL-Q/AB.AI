# ТЗ для бэкенд-разработчика: AB-AI.kz

## 1. О проекте

AB-AI.kz — SaaS-платформа для автосервисов Казахстана. AI-агент проактивно обращается к прошлым клиентам (retention), отвечает на входящие сообщения, напоминает о ТО. Владелец видит все действия на дашборде и может управлять AI.

**Стек:** FastAPI + PostgreSQL + Redis + Celery + OpenAI API

**Валюта:** KZT (тенге). Цены уточняются, пока заглушки: Start = 0₸, Pro = 14 990₸, Business = 39 990₸.

---

## 2. Запуск и окружение

```
docker-compose up -d
```

5 сервисов: PostgreSQL (5433), Redis (6380), uvicorn (8001), celery-worker, celery-beat.

### Критичные нюансы

- PostgreSQL и Redis на нестандартных портах (5433, 6380) — конфликт с другим проектом
- Celery worker **обязательно** `--pool=solo` — `asyncio.run()` несовместим с prefork
- `.env` в корне проекта, загружается через `pydantic-settings` с абсолютным путём
- Celery-таски: после каждого `asyncio.run()` вызывается `_dispose_engine()` для очистки asyncpg-пулов

### Команды для локальной разработки

```bash
# Backend
cd backend
python -m uvicorn app.main:app --port 8001

# Celery worker
celery -A app.tasks.celery_app:celery_app worker --loglevel=info --pool=solo

# Celery beat
celery -A app.tasks.celery_app:celery_app beat --loglevel=info

# Frontend
cd frontend-web
npm run dev

# Миграции
alembic revision --autogenerate -m "описание"
alembic upgrade head
```

---

## 3. Биллинг и подписки

### Архитектура (гибридная)

Два способа оплаты:

1. **Автосписание (рекуррент)** — клиент привязывает карту, каждый месяц списывается автоматически через YooKassa
2. **Оплата по ссылке** — система шлёт ссылку на оплату (Kaspi Pay / Halyk Pay). Не требует привязки карты

### Провайдеры

| Провайдер | Назначение | Статус |
|---|---|---|
| YooKassa | Рекуррентные автоплатежи, токенизация карт, работает в СНГ и КЗ | Приоритет #1, stub готов |
| Kaspi Pay | Разовые оплаты по ссылке, самый популярный в КЗ | Stub, нужна интеграция после получения ИП |
| Halyk Pay | Разовые оплаты, резерв | Не начат |

### Тарифы (KZT, цены уточняются)

| Тариф | ₸/мес | Клиентов | AI-сообщений | Каналы | Дополнительно |
|---|---|---|---|---|---|
| Start | 0 | 100 | 200 | Telegram | Базовый AI-ответчик |
| Pro | 14 990 | 1 000 | 2 000 | Все | AI auto + semi_auto, сервисные интервалы, метрики удержания |
| Business | 39 990 | Безлимит | Безлимит | Все | API-интеграции, приоритетная поддержка |

### Фаза 1 (до ИП) — текущее состояние

Биллинг не принимает реальные платежи. Модель `Subscription` уже есть в БД (plan, status, trial_ends_at, external_id). API возвращает заглушку при попытке checkout. **Задача:** подготовить архитектуру для YooKassa, чтобы после получения мерчанта подключить за 1-2 дня.

### Что нужно реализовать

- `billing_service.py` — заменить заглушки на реальные YooKassa API-вызовы:
  - `create_checkout_session()` → YooKassa Payment API
  - `handle_yookassa_webhook()` → YooKassa Webhooks (payment.succeeded, recurring.succeeded, recurring.canceled)
  - `cancel_subscription()` → YooKassa Recurring API
- `POST /billing/checkout` — принимает `plan` и `payment_method` (`yookassa` | `kaspi`), возвращает ссылку на оплату
- `POST /billing/webhooks/yookassa` — обработка вебхуков, обновление статуса подписки
- **Enforcement dependency** — `RequireActiveSubscription`:
  - Start: макс. 100 клиентов, 200 AI-сообщений/мес, 1 канал (Telegram)
  - Pro: макс. 1000 клиентов, 2000 сообщений, все каналы
  - Business: безлимит
  - Проверка происходит на уровне API-эндпоинтов (FastAPI dependency injection)
- **Счётчик AI-сообщений** — каждый AI-ответ инкрементит `Subscription.ai_messages_used` (новая колонка + миграция), раз в месяц сбрасывается через Celery beat

---

## 4. Каналы связи

| Канал | Провайдер | Статус | Что доработать |
|---|---|---|---|
| Telegram | Telegram Bot API | ✅ E2E работает | — |
| WhatsApp | Twilio | ✅ Код готов | Sandbox-тест → продакшн апрув Twilio |
| SMS | Twilio | ✅ Код готов | Реальные креды для продака |

Twilio закрывает и WhatsApp, и SMS одними кредами. Входящие WhatsApp-вебхуки приходят как `form-urlencoded` (Twilio формат).

---

## 5. Задачи по приоритету

### P0 — Критичное (до первого клиента)

1. **YooKassa интеграция** — заменить заглушки на реальные API-вызовы в `billing_service.py`, реализовать checkout + webhooks + recurring
2. **Enforcement — ограничение по тарифу** — dependency `RequireActiveSubscription`, лимиты клиентов/сообщений/каналов
3. **Счётчик AI-сообщений** — колонка `ai_messages_used` в Subscription, инкремент при AI-ответе, ежемесячный сброс через Celery beat
4. **Тесты** — 0 автотестов. Минимум: auth flow, inbound webhook → AI reply, outreach pipeline, billing checkout
5. **Email-отчёты** — `report_service.py` генерирует HTML, но не отправляет. Нужна интеграция с Resend (ключ `RESEND_API_KEY` уже в конфиге)

### P1 — Важное (до масштабирования)

6. **Мультиарендность guard** — проверить что `team_id` из JWT совпадает с запрашиваемым ресурсом. Сейчас почти все эндпоинты фильтруют по `team_id`, но нет валидации что юзер принадлежит этой команде
7. **Обработка медиа** — входящие фото/файлы не обрабатываются. Загрузка в S3 (конфиг есть), ссылка в сообщении
8. **Graceful fallback при отсутствии OpenAI ключа** — записывать входящее сообщение в БД, но не крашить при ошибке генерации AI-ответа
9. **Rate limiting** — slowapi подключён, но лимиты не настроены для конкретных эндпоинтов (логин, создание клиентов, AI-ответы)
10. **Production-ready** — SECRET_KEY из env, HTTPS, CORS для прод-домена, HEALTHCHECK в Docker

### P2 — Желаемое

11. **Дашборд с реальными данными** — агрегация: новые клиенты за неделю, выручка, возвратность, активные диалоги
12. **Экспорт данных** — CSV/XLSX выгрузка клиентов, визитов, отчётов
13. **Push-уведомления** — мобильное приложение получает пуши при: новом сообщении, эскалации, завершении импорта
14. **Настройка каналов через UI** — сейчас WhatsApp/Telegram/SMS показывают «Скоро», нужна страница подключения ботов/номеров
15. **API-документация** — Swagger на `/docs`, добавить примеры и описания на русском

---

## 6. Структура проекта

```
backend/
  app/
    api/v1/           # 18 роутеров (auth, clients, cars, visits, imports,
                      #   campaigns, templates, conversations, messages,
                      #   ai-agent, analytics, billing, notifications,
                      #   settings, service-intervals, realtime, webhooks, me)
    core/             # config.py, security.py, deps.py, limiter.py, permissions.py, exceptions.py
    db/               # models/ (17 моделей), session.py, base.py, migrations/
    realtime/         # bus.py (EventBus), events.py
    schemas/          # Pydantic schemas
    services/         # 23 сервиса (бизнес-логика)
    tasks/            # 9 модулей Celery задач + celery_app.py
    templates/        # HTML-шаблоны (weekly_report.html)

frontend-web/         # Next.js 15, React 19, TailwindCSS, Radix UI
  app/(app)/          # 10 страниц + service-intervals
  components/         # UI-компоненты + диалоги форм
  hooks/              # use-websocket.ts, use-me.ts
  lib/                # api.ts, auth.ts, formatters.ts, utils.ts

mobile/               # Expo React Native (stub)
  app/                # (auth)/login + (tabs)/5 экранов
  lib/, stores/       # api.ts, types.ts, auth.ts
```

---

## 7. Ключевые технические решения

### 7.1. Celery + asyncio

Каждая задача вызывает `asyncio.run()` + `_dispose_engine()` в `finally`. Без dispose — утечка asyncpg-коннектов между тасками. Worker строго `--pool=solo`.

```python
@celery_app.task(name="app.tasks.outreach.run_outreach_cycle")
def run_outreach_cycle_task() -> None:
    try:
        asyncio.run(_run_outreach_for_all_teams())
    except Exception:
        logging.exception("run_outreach_cycle_task crashed")
    finally:
        try:
            asyncio.run(_dispose_engine())
        except Exception:
            pass
```

### 7.2. Вебхуки без SessionDep

`record_inbound_message()` создаёт свою сессию и коммитит **до** dispatch Celery. Иначе ExclusiveLock на строке conversation блокирует Celery-воркер.

### 7.3. EventBus

`bus.publish()` — только в FastAPI контексте. В Celery — `publish_nowait()`. EventBus детектит смену event loop и пересоздаёт Redis publisher.

### 7.4. AI-агент по умолчанию `auto`

Ответы отправляются сразу. `semi_auto` — черновики требуют одобрения через `/ai-agent/outreach/{id}/approve`.

### 7.5. Outreach pipeline

Celery beat каждый час → `_get_outreach_candidates()` → LLM решает кому писать → `channel_dispatcher` → WhatsApp/Telegram/SMS. Кулдаун 24ч, эскалация после 2 неотвеченных.

### 7.6. WhatsApp через Twilio

Отправка: префикс `whatsapp:` к номеру, Twilio Messages API. Входящие: `form-urlencoded` вебхук. Не нужен отдельный Meta/360dialog аккаунт.

---

## 8. Celery beat расписание

| Имя | Таска | Расписание |
|---|---|---|
| run-outreach-cycle-every-hour | `app.tasks.outreach.run_outreach_cycle` | Каждый час :00 |
| check-escalations-every-hour | `app.tasks.outreach.check_escalations` | Каждый час :30 |
| evaluate-campaign-triggers | `app.tasks.campaigns.evaluate_triggers` | Каждые 15 минут |
| run-feedback-loop-every-6-hours | `app.tasks.feedback.run_feedback_loop` | Каждые 6 часов :00 |
| generate-weekly-reports | `app.tasks.reports.weekly_report` | Каждый понедельник 09:00 UTC |

---

## 9. Конфигурация (все переменные .env)

```
# App
APP_ENV=development
APP_URL=http://localhost:3000
SECRET_KEY=change-me-in-production
TEAM_SLUG_DEFAULT=default
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:8081"]

# Database
DATABASE_URL=postgresql+asyncpg://abai:abai@localhost:5433/abai
DATABASE_SYNC_URL=postgresql://abai:abai@localhost:5433/abai

# Redis
REDIS_URL=redis://localhost:6380/0
CELERY_BROKER_URL=redis://localhost:6380/1
CELERY_RESULT_BACKEND=redis://localhost:6380/2

# JWT
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Twilio (SMS + WhatsApp)
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=

# Telegram
TELEGRAM_BOT_TOKEN=

# Shared secret for inbound webhooks
INBOUND_WEBHOOK_SECRET=

# LLM
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Email
RESEND_API_KEY=
EMAIL_FROM=noreply@ab-ai.kz

# Storage (Cloudflare R2 / S3)
S3_ENDPOINT=
S3_ACCESS_KEY=
S3_SECRET_KEY=
S3_BUCKET=ab-ai

# Billing (Kazakhstan)
YOOKASSA_SHOP_ID=
YOOKASSA_SECRET_KEY=
KASPI_MERCHANT_ID=
KASPI_API_KEY=

# Monitoring
SENTRY_DSN=
POSTHOG_API_KEY=
```

---

## 10. Существующие баги/нюансы

| # | Описание | Приоритет |
|---|---|---|
| 1 | Pydantic v2 сериализует Decimal как float, фронтенд ожидает string для `total_spent`, `total_amount`, `resulted_in_revenue` | P1 |
| 2 | `ImportLogOut.errors` — нетипизированный `list` вместо `list[ImportErrorRow]` | P2 |
| 3 | Настройки каналов в UI показывают «Скоро» | P2 |
| 4 | Mobile app — stub, не подключён к API | P2 |
| 5 | YooKassa webhook не проверяет подпись (нужна реализация verify_signature) | P0 (вместе с интеграцией) |

---

## 11. Процесс разработки

- Ветка: `feat/ai-auto-reply` (текущая), PR в `main`
- Коммиты: английский, формат `type: description`
- Проверка: `npm run build` (frontend) + `python -c "from app.main import app"` (backend import check)
- Миграции: `alembic revision --autogenerate -m "описание"`
- Python: 3.12+, Node: 20+

---

## 12. Ключевые константы

| Константа | Файл | Значение |
|---|---|---|
| COOLDOWN_HOURS | outreach_service.py | 24 |
| MAX_UNANSWERED_BEFORE_ESCALATE | outreach_service.py | 2 |
| OUTREACH_MAX_TOKENS | outreach_service.py | 600 |
| REPLY_CONTEXT_MESSAGES | ai_agent_service.py | 20 |
| MAX_REPLY_TOKENS | ai_agent_service.py | 400 |
| access_token_expire_minutes | config.py | 60 |
| refresh_token_expire_days | config.py | 30 |