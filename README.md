# Telegram RAG Bot

Проект содержит Telegram-бота на aiogram 3.x c оплатой в Stars, триалом, личным кабинетом и формой поддержки.

## Запуск

1. Создайте `.env`:
   ```env
   BOT_TOKEN=000:token
   ADMIN_CHAT_ID=123456
   BILLING_BASE_URL=https://billing.internal
   PROVISIONER_BASE_URL=https://provisioner.internal
   PAYMENT_PROVIDER_TOKEN=STARS
   ```
2. Установите зависимости и запустите:
   ```bash
   pip install -r requirements.txt
   python main.py
   ```

Бот поддерживает команды `/start` и `/trial`, навигацию по меню, выдачу конфигураций из provisioner и создание тикетов в поддержку.
