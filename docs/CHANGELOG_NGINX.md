# 🔧 Исправление: Flask + Nginx Integration

## ✅ Что было исправлено

### 1. Конфигурация портов
- **До**: Несогласованные порты (8000 в Docker, 5000 в Flask, 80 в Nginx)
- **После**: 
  - Flask: `0.0.0.0:5000`
  - Nginx: порт 80 → проксирует на `127.0.0.1:5000`

### 2. Конфигурация Nginx
**Файл**: [nginx/conf.d/dubaigemmsgifts.sbs.conf](nginx/conf.d/dubaigemmsgifts.sbs.conf)

Добавлено:
- ✅ Таймауты (60s) для длительных запросов
- ✅ Дополнительные прокси-заголовки
- ✅ Отключение буферизации для SSE/long-polling
- ✅ Поддержка WebSocket
- ✅ Кеширование статических файлов

### 3. Flask приложение
**Файлы**: [run.py](run.py), [start.py](start.py)

Улучшения:
- ✅ `threaded=True` для обработки одновременных запросов
- ✅ Логирование запуска
- ✅ Трассировка ошибок

### 4. Docker конфигурация
**Файлы**: [docker-compose.yml](docker-compose.yml), [Dockerfile](Dockerfile)

Изменения:
- ✅ Порты: `5000:5000` (Flask) и `80:80` (Nginx)
- ✅ Экспорт обоих портов

### 5. Автоматизация и скрипты

Созданы скрипты для упрощения работы:

| Скрипт | Назначение |
|--------|------------|
| [`scripts/test_connection.sh`](scripts/test_connection.sh) | Проверка соединения Flask ↔ Nginx |
| [`scripts/run_flask.sh`](scripts/run_flask.sh) | Быстрый запуск Flask для разработки |
| [`scripts/run_all.sh`](scripts/run_all.sh) | Запуск всех сервисов (Flask + Bot + Nginx) |
| [`scripts/setup_nginx.sh`](scripts/setup_nginx.sh) | Настройка Nginx на хост-машине |
| [`deploy/deploy_production.sh`](deploy/deploy_production.sh) | Полное развертывание для production |

### 6. Документация

Созданы подробные руководства:

| Документ | Описание |
|----------|----------|
| [docs/QUICKSTART_NGINX.md](docs/QUICKSTART_NGINX.md) | Быстрый старт (3 шага) |
| [docs/NGINX_FLASK_SETUP.md](docs/NGINX_FLASK_SETUP.md) | Полная документация с решением проблем |
| [deploy/bottgpanel.service](deploy/bottgpanel.service) | Systemd service для production |

## 🚀 Как использовать

### Вариант 1: Быстрый старт (Разработка)

```bash
# 1. Настройка Nginx (один раз)
sudo ./scripts/setup_nginx.sh

# 2. Запуск Flask
./scripts/run_flask.sh

# 3. Проверка
./scripts/test_connection.sh
```

### Вариант 2: Все сервисы одновременно

```bash
sudo ./scripts/run_all.sh
```

### Вариант 3: Production развертывание

```bash
sudo ./deploy/deploy_production.sh
```

## 📊 Архитектура

```
┌──────────────┐
│   Клиент     │
│  (Браузер)   │
└──────┬───────┘
       │ HTTP :80
       ▼
┌──────────────┐
│    Nginx     │ ← Reverse Proxy
│   (Port 80)  │   - Проксирование
└──────┬───────┘   - Кеширование
       │            - SSL (опционально)
       │ HTTP :5000
       ▼
┌──────────────┐
│    Flask     │ ← Веб-приложение
│  (Port 5000) │   + Gunicorn (prod)
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Telegram Bot │ ← Обработка сообщений
└──────────────┘
```

## 🔍 Диагностика

### Проверка сервисов

```bash
# Автоматическая проверка
./scripts/test_connection.sh

# Ручная проверка
curl http://localhost:5000  # Flask напрямую
curl http://localhost:80    # Через Nginx

# Процессы
sudo lsof -i :5000  # Flask
sudo lsof -i :80    # Nginx
```

### Логи

```bash
# Flask (если запущен как systemd service)
sudo journalctl -u bottgpanel -f

# Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 🛠️ Решение проблем

### 502 Bad Gateway
**Причина**: Flask не запущен или недоступен

**Решение**:
```bash
# Проверьте Flask
curl http://localhost:5000

# Перезапустите Flask
python run.py
```

### Connection refused
**Причина**: Nginx не может подключиться к Flask

**Решение**:
```bash
# Убедитесь, что Flask слушает 0.0.0.0
# В run.py должно быть: app.run(host="0.0.0.0", port=5000)

# Проверьте firewall
sudo ufw allow 5000
```

### Port already in use
**Причина**: Порт занят другим процессом

**Решение**:
```bash
# Найдите процесс
sudo lsof -i :5000  # для Flask
sudo lsof -i :80    # для Nginx

# Убейте процесс
sudo kill -9 <PID>
```

## 📦 Структура изменений

```
BotTGPanel/
├── nginx/conf.d/
│   └── dubaigemmsgifts.sbs.conf  ← Обновлено
├── scripts/
│   ├── test_connection.sh         ← Новый
│   ├── run_flask.sh               ← Новый
│   ├── run_all.sh                 ← Новый
│   └── setup_nginx.sh             ← Новый
├── deploy/
│   ├── bottgpanel.service         ← Новый
│   └── deploy_production.sh       ← Новый
├── docs/
│   ├── QUICKSTART_NGINX.md        ← Новый
│   ├── NGINX_FLASK_SETUP.md       ← Новый
│   └── CHANGELOG_NGINX.md         ← Этот файл
├── run.py                         ← Обновлено
├── start.py                       ← Обновлено
├── docker-compose.yml             ← Обновлено
├── Dockerfile                     ← Обновлено
└── requirements.txt               ← Обновлено (+ gunicorn)
```

## 🎯 Итог

Теперь Flask правильно интегрирован с Nginx:

✅ Flask запускается на `0.0.0.0:5000`  
✅ Nginx слушает порт 80 и проксирует на Flask  
✅ Все заголовки правильно передаются  
✅ Поддержка WebSocket и long-polling  
✅ Автоматические скрипты для управления  
✅ Готово к production развертыванию  

## 📚 Дополнительная информация

- [Быстрый старт](docs/QUICKSTART_NGINX.md)
- [Полная документация](docs/NGINX_FLASK_SETUP.md)
- [Troubleshooting Gift Transfers](docs/TROUBLESHOOTING_GIFT_TRANSFERS.md)

## 🤝 Поддержка

Если остались вопросы:
1. Запустите `./scripts/test_connection.sh`
2. Проверьте логи Nginx
3. Изучите документацию в `docs/`
