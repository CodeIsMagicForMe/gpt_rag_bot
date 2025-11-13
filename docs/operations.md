# Операционное руководство

## Мониторинг
- На каждом узле установлен Netdata с включённым экспортом метрик для Prometheus по адресу `http://<node>:19999/netdata/api/v1/allmetrics?format=prometheus`. Экспортируются стандартные метрики ЦП/памяти, показатели WireGuard (`go.d/wireguard`) и OpenVPN (`python.d/openvpn`), а также метрики потерь/RTT из `fping`.
- Список целевых хостов для измерения RTT задаётся переменной `netdata_latency_targets`. Для каждого элемента настроены тревоги на рост RTT и потерю пакетов. Значения порогов по умолчанию: предупреждение после 120 мс, критика после 250 мс.
- Provisioner отправляет счётчик ошибок в StatsD (`provisioner.provision.error`), Netdata отслеживает и шлёт уведомления в Telegram через `health_alarm_notify.conf`.

## VPN-телеметрия
- Скрипт `/usr/local/bin/vpn-log-exporter.py` запускается systemd-таймером `vpn-log-exporter.timer` каждые 5 минут.
- Логи пишутся в `/var/log/vpn/vpn-telemetry.log` в формате JSON. Для анонимизации все идентификаторы (пиры, адреса) хэшируются SHA-256 и усекаются до 16 символов.
- Журналы ротируются через `/etc/logrotate.d/vpn-telemetry`.

## Резервное копирование
- Скрипт `/usr/local/bin/vpn-backup.sh` запускается systemd-таймером `vpn-backup.timer` ежедневно в 03:30 UTC.
- Бэкап включает:
  - `pg_dump` базы данных `billing` из контейнера Docker (привязка по label `com.docker.compose.project=platform` и сервису `db`).
  - Архив конфигураций (`/etc/wireguard`, `/etc/openvpn`, `/opt/amneziawg`, `/etc/smartdns`, `/opt/platform/docker-compose.yml`, `/opt/platform/.env`) в `configs.tar.gz`.
  - Контрольную сумму (`SHA256SUMS`).
- Результат складывается в `/var/backups/vpn` и отправляется в Object Storage с помощью `rclone` в бакет `vpn-journald-backups` (путь `<hostname>/<timestamp>`). Локальные бэкапы старше 14 дней удаляются.

### Запуск вручную
```bash
sudo systemctl start vpn-backup.service
journalctl -u vpn-backup.service -b
```

## Проверка восстановления
- Таймер `vpn-backup-restore.timer` запускает `/usr/local/bin/vpn-backup-restore.sh` дважды в месяц (1-го и 15-го числа в 04:00 UTC).
- Скрипт выбирает последний локальный бэкап, поднимает временный контейнер `postgres:15`, создаёт базу `billing_restore` и выполняет `pg_restore`. При успехе контейнер удаляется, результат фиксируется в `/var/log/vpn/vpn-backup-restore.log`.

### Тест восстановления вручную
```bash
sudo systemctl start vpn-backup-restore.service
journalctl -u vpn-backup-restore.service -b
```

## Восстановление из бэкапа
1. Выбрать нужный архив в Object Storage: `backups:vpn-journald-backups/<hostname>/<timestamp>/`.
2. Скачать каталог: `rclone copy backups:vpn-journald-backups/<hostname>/<timestamp> /tmp/restore`.
3. Остановить сервисы: `sudo systemctl stop bot billing provisioner` и `docker compose -p platform -f /opt/platform/docker-compose.yml stop`.
4. Восстановить БД:
   ```bash
   docker compose -p platform -f /opt/platform/docker-compose.yml exec -T db pg_restore -U billing -d billing --clean --create /tmp/billing.dump
   ```
   (при необходимости сначала загрузить файл в контейнер: `docker cp /tmp/restore/billing.dump $(docker ps --filter label=com.docker.compose.service=db --format "{{'{{'}}.ID{{'}}'}}"):/tmp/billing.dump`).
5. Распаковать конфигурации: `sudo tar -xzf /tmp/restore/configs.tar.gz -C /`.
6. Запустить сервисы и проверить статус: `sudo systemctl start bot billing provisioner` и `systemctl status vpn-backup.service`.
