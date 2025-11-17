# AB.AI — Aqyldy Business AI Assistant

AB.AI is a platform for creating intelligent AI assistants for small businesses (cafés, hotels, service companies).
The mission of the project is to provide entrepreneurs with a virtual employee who answers customers 24/7, speaks multiple languages, and helps increase revenue.


## Overview

AB.AI transforms the process of creating a business-specific AI into a simple, guided onboarding flow inside Telegram.
No coding required. The assistant is generated automatically based on the business profile.


## Features

### Smart Onboarding
Owners answer questions about:
- business type
- name & location
- menu or services
- working hours
- supported languages
- contact channels

The platform generates a BusinessProfile, which trains the AI assistant.

### Automatic System Prompt Generation
AB.AI builds a detailed prompt containing:
- assistant personality
- business context
- service/menu knowledge
- multilingual support

### Demo Mode
Business owners can immediately test their AI assistant.

### Help Mode
Guided instructions for:
- configuration
- improving responses
- updating business information

### User State Tracking
The platform remembers onboarding progress and resumes seamlessly.

### AI-Powered Telegram Bot
The assistant replies:
- instantly
- contextually
- in multiple languages
- using OpenAI models


## Tech Stack

- Backend — FastAPI (Python)
- Database — SQLModel (SQLite / PostgreSQL)
- AI Engine — OpenAI Chat Completions API
- Messaging — Telegram Bot API (Webhook)
- Infrastructure — uvicorn, ngrok / custom domain
- Optional — Docker


## Project Structure

```bash
app/
  config.py
  db.py
  models.py
  schemas.py
  services/
    ai.py
    analytics.py
  routers/
    bots.py
    analytics.py
    telegram.py
  main.py

.env.example
README.md
```

## Environment Variables

```env
OPENAI_API_KEY=your_openai_key_here
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=sqlite:///./abai.db
AI_MODEL=gpt-5.1-mini
NGROK_PUBLIC_URL=https://your-ngrok-or-domain
ENV=development
```

## Local Development

1. Install dependencies:
pip install -r requirements.txt

2. Create a virtual environment:
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

3. Run the development server:
uvicorn app.main:app --reload

4. URLs:
http://localhost:8000
http://localhost:8000/docs


## Telegram Bot Setup

- Create a bot via @BotFather
- Add the token to .env
- Set the webhook: https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/setWebhook?url=https://YOUR_DOMAIN/telegram/webhook

- Telegram will send updates to: POST /telegram/webhook


## Roadmap

Completed:
- Business onboarding
- BusinessProfile generation
- Telegram webhook
- OpenAI-based AI engine
- Demo mode
- Help mode
- UserState system

Coming soon:
- Web dashboard
- WhatsApp & Instagram support
- Multi-tenant mode
- Live chat & history
- ROI analytics
- Templates for cafés, hotels, and service businesses


## Vision

AB.AI is built for business owners who want:
- fewer routine tasks
- automated customer conversations
- multilingual AI
- increased revenue

AB.AI aims to function as a virtual employee.


## ❤️ Contributing

Contributions are welcome.
Open an Issue or submit a Pull Request.

