# 🔌 Flask + Nginx Integration

## Быстрый старт

```bash
# 1. Настройка (один раз)
sudo ./scripts/setup_nginx.sh

# 2. Запуск
python run.py

# 3. Проверка
./scripts/test_connection.sh
```

## Архитектура

```
Клиент → Nginx (:80) → Flask (:5000) → Telegram Bot
```

## Скрипты

- `scripts/test_connection.sh` - проверка соединения
- `scripts/run_flask.sh` - запуск Flask
- `scripts/run_all.sh` - запуск всех сервисов
- `scripts/setup_nginx.sh` - настройка Nginx

## Документация

- [Быстрый старт](docs/QUICKSTART_NGINX.md) - 3 шага
- [Полная инструкция](docs/NGINX_FLASK_SETUP.md) - со всеми деталями
- [Список изменений](docs/CHANGELOG_NGINX.md) - что было исправлено

## Production

```bash
sudo ./deploy/deploy_production.sh
```

Автоматически настроит:
- Gunicorn (WSGI server)
- Systemd service
- Nginx
- Firewall

## Проверка

```bash
curl http://localhost:5000  # Flask напрямую
curl http://localhost:80    # Через Nginx
```
