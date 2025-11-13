# GPT RAG Bot Subscriptions Service

Этот репозиторий дополнен микросервисом подписок на FastAPI + SQLAlchemy.

## Быстрый старт

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Основные возможности

- Таблицы `users`, `plans`, `subscriptions`, `payments`, `promocodes`, `referrals` с миграциями Alembic.
- REST эндпоинты:
  - `POST /payments/stars/confirm` — подтверждение платежа звёздами и продление подписки.
  - `POST /trial/start` — активация пробного периода плана.
  - `POST /promocode/apply` — применение промокода.
  - `GET /subs/status` — получение статуса подписки пользователя.
- Поддержка grace-периода, автопродлений и начисления бонусов реферальной программы.
- Утилита `app/jobs/reminders.py` для рассылки напоминаний об окончании подписок через Telegram API.
- Юнит-тесты логики подписок (`pytest`).
