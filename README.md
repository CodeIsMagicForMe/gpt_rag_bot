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

## Provisioner API

В репозитории также есть FastAPI‑сервис `provisioner`, отвечающий за выдачу VPN‑конфигураций. Он управляет метаданными узлов, пулом ключей, взаимодействует с WireGuard (через `wgctrl`), OpenVPN (easy-rsa), Amnezia CLI и загружает файлы/QR в S3.

### Переменные окружения

```
DATABASE_URL=sqlite:///./provisioner.db
S3_BUCKET=bucket
S3_ACCESS_KEY=key
S3_SECRET_KEY=secret
S3_REGION=us-east-1
MAX_DEVICES_PER_USER=3
```

### Запуск

```
python -m provisioner.main
```

Основные эндпоинты:

* `POST /provision` — выдача нового устройства, с генерацией QR и ссылок на файлы в S3.
* `POST /revoke` — отзыв и освобождение ключа.
* `POST /switch_node` — переключение узла.
* `POST /stats/peers` — обновление статистики активных пиров.
* `GET /nodes` — список доступных узлов.
* `GET /metrics` — метрики Prometheus, дополнительно события отправляются в StatsD.
