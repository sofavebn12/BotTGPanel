# Быстрый старт: Flask + Nginx

## Проблема
Flask не подхватывается при запуске через Nginx на порту 80.

## Решение (3 простых шага)

### 1️⃣ Настройка Nginx (один раз)

```bash
sudo ./scripts/setup_nginx.sh
```

Этот скрипт:
- Установит Nginx (если не установлен)
- Скопирует конфигурацию в `/etc/nginx/sites-available/`
- Создаст символическую ссылку в `/etc/nginx/sites-enabled/`
- Проверит конфигурацию
- Перезагрузит Nginx

### 2️⃣ Запуск Flask

**Вариант A: Только Flask (рекомендуется для разработки)**
```bash
./scripts/run_flask.sh
# или
python run.py
```

**Вариант B: Все сервисы (Flask + Bot + Nginx)**
```bash
sudo ./scripts/run_all.sh
# или
sudo python start.py
```

### 3️⃣ Проверка

```bash
./scripts/test_connection.sh
```

Или проверьте вручную:
```bash
# Flask напрямую
curl http://localhost:5000

# Через Nginx
curl http://localhost:80
```

Откройте браузер:
- `http://localhost` (через Nginx)
- `http://localhost:5000` (напрямую Flask)

## Архитектура

```
┌─────────┐       ┌────────────┐       ┌─────────────┐
│ Клиент  │──────▶│ Nginx :80  │──────▶│ Flask :5000 │
└─────────┘       └────────────┘       └─────────────┘
                   reverse proxy         веб-сервер
```

## Полезные скрипты

| Скрипт | Описание |
|--------|----------|
| `scripts/setup_nginx.sh` | Настройка Nginx (один раз) |
| `scripts/run_flask.sh` | Запуск только Flask |
| `scripts/run_all.sh` | Запуск всех сервисов |
| `scripts/test_connection.sh` | Проверка соединения |

## Устранение проблем

### Flask не отвечает
```bash
# Проверьте порт
sudo lsof -i :5000

# Убейте процесс, если нужно
sudo kill -9 <PID>

# Запустите заново
python run.py
```

### Nginx выдает 502 Bad Gateway
```bash
# Убедитесь, что Flask запущен
curl http://localhost:5000

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/error.log
```

### Порт 80 занят
```bash
# Найдите процесс
sudo lsof -i :80

# Убейте его
sudo kill -9 <PID>
```

## Подробная документация

Полная документация: [docs/NGINX_FLASK_SETUP.md](docs/NGINX_FLASK_SETUP.md)

## Production

Для production используйте Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

Или создайте systemd service (см. документацию).

## Мониторинг

```bash
# Статус Nginx
sudo systemctl status nginx

# Логи в реальном времени
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Процессы
ps aux | grep python
ps aux | grep nginx
```
