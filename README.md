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
   TERMS_URL=https://example.com/terms
   PRIVACY_URL=https://example.com/privacy
   DATA_USAGE_NOTICE="ℹ️ Мы храним только ваш Telegram ID и технические метаданные для работы сервиса."
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
S3_SSE_ALGORITHM=AES256
# S3_SSE_KMS_KEY_ID=<опционально: ARN KMS-ключа>
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

## SmartDNS

В репозитории есть отдельный сервис SmartDNS на базе `dnslib`, который умеет подменять IP‑адреса для целевых доменов и отдавать остальные запросы через публичные DNS.

Возможности:

* Загрузка правил из таблицы `smartdns_rules` (SQLAlchemy модель присутствует в `db/models.py`) и/или из файла формата `domain ip [ttl]`.
* Горячий перезапуск правил по таймеру без остановки DNS‑сервера.
* Мониторинг доступности (постоянный запрос домена) и метрики Prometheus (`/metrics` поднимается через встроенный HTTP‑сервер библиотеки).

### Конфигурация

Через переменные окружения (есть поддержка `.env`):

```
SMARTDNS_HOST=0.0.0.0
SMARTDNS_PORT=1053
SMARTDNS_ENABLE_TCP=true
SMARTDNS_RULES_BACKEND=auto        # db | file | both | auto
SMARTDNS_RULES_FILE=/etc/smartdns.rules
SMARTDNS_RELOAD_INTERVAL=30
SMARTDNS_UPSTREAMS=1.1.1.1:53,8.8.8.8:53
SMARTDNS_METRICS_HOST=0.0.0.0
SMARTDNS_METRICS_PORT=9105
SMARTDNS_MONITOR_DOMAIN=example.com
SMARTDNS_MONITOR_HOST=127.0.0.1
SMARTDNS_MONITOR_PORT=1053
DATABASE_URL=sqlite:///./provisioner.db
```

### Запуск

```
python -m smartdns.main
```
