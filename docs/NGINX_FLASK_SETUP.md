# Настройка Nginx и Flask для проксирования

## Проблема
Когда вы запускаете трансляцию через Nginx на своем сервере (порт 80), Flask не подхватывается.

## Решение

### 1. Архитектура
```
Клиент -> Nginx (порт 80) -> Flask (порт 5000)
```

Nginx выступает как reverse proxy и перенаправляет все запросы на Flask.

### 2. Измененные файлы

#### `nginx/conf.d/dubaigemmsgifts.sbs.conf`
```nginx
server {
    listen 80;
    server_name dubaigemmsgifts.sbs;
    
    # Увеличиваем таймауты
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;

    location / {
        proxy_pass http://127.0.0.1:5000;  # Проксируем на Flask
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Отключаем буферизацию
        proxy_buffering off;
        proxy_cache off;
    }
}
```

#### `run.py`
```python
if __name__ == "__main__":
    print("[Flask] Starting Flask server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
```

#### `docker-compose.yml`
```yaml
ports:
  - "5000:5000"  # Flask port
  - "80:80"      # Nginx port
```

### 3. Запуск

#### Вариант A: С Nginx на хост-машине (рекомендуется)

1. **Запустите Flask:**
   ```bash
   python run.py
   ```
   Flask будет слушать на `0.0.0.0:5000`

2. **Настройте Nginx на хост-машине:**
   ```bash
   # Скопируйте конфигурацию
   sudo cp nginx/conf.d/dubaigemmsgifts.sbs.conf /etc/nginx/sites-available/
   sudo ln -s /etc/nginx/sites-available/dubaigemmsgifts.sbs.conf /etc/nginx/sites-enabled/
   
   # Удалите дефолтную конфигурацию (если есть)
   sudo rm /etc/nginx/sites-enabled/default
   
   # Проверьте конфигурацию
   sudo nginx -t
   
   # Перезагрузите Nginx
   sudo systemctl reload nginx
   ```

3. **Откройте браузер:**
   ```
   http://dubaigemmsgifts.sbs
   # или
   http://your-server-ip
   ```

#### Вариант B: С автоматическим запуском всех сервисов

```bash
sudo python start.py
```

Это запустит:
- Flask на порту 5000
- Telegram бот
- Nginx на порту 80

### 4. Проверка соединения

Запустите скрипт проверки:

```bash
chmod +x scripts/test_connection.sh
./scripts/test_connection.sh
```

Или проверьте вручную:

```bash
# Проверка Flask напрямую
curl http://localhost:5000

# Проверка через Nginx
curl http://localhost:80

# Проверка процессов
sudo lsof -i :5000  # Flask
sudo lsof -i :80    # Nginx
```

### 5. Возможные проблемы и решения

#### Проблема: Flask не запускается
```bash
# Проверьте, что порт 5000 свободен
sudo lsof -i :5000
# Если занят, убейте процесс
sudo kill -9 <PID>
```

#### Проблема: Nginx не может подключиться к Flask
```bash
# Убедитесь, что Flask слушает на 0.0.0.0, а не на 127.0.0.1
# В run.py должно быть: app.run(host="0.0.0.0", port=5000)

# Проверьте firewall
sudo ufw allow 5000
sudo ufw allow 80
```

#### Проблема: 502 Bad Gateway
```bash
# Проверьте, что Flask запущен
curl http://localhost:5000

# Проверьте логи Nginx
sudo tail -f /var/log/nginx/error.log

# Проверьте, что Nginx может подключиться к Flask
sudo -u www-data curl http://localhost:5000
```

#### Проблема: Порт 80 требует sudo
```bash
# Вариант 1: Запустите с sudo
sudo python start.py

# Вариант 2: Используйте Nginx системный (рекомендуется)
sudo systemctl start nginx
python run.py  # Flask без sudo
```

#### Проблема: Nginx не видит изменения в конфигурации
```bash
# Проверьте синтаксис
sudo nginx -t

# Перезагрузите Nginx
sudo systemctl reload nginx
# или
sudo nginx -s reload
```

### 6. Производственная среда (Production)

Для production используйте:

1. **Gunicorn вместо Flask dev server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 run:app
   ```

2. **Создайте systemd service:**
   ```bash
   sudo nano /etc/systemd/system/bottgpanel.service
   ```
   
   ```ini
   [Unit]
   Description=BotTGPanel Flask App
   After=network.target

   [Service]
   User=youruser
   WorkingDirectory=/path/to/BotTGPanel
   Environment="PATH=/path/to/venv/bin"
   ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable bottgpanel
   sudo systemctl start bottgpanel
   ```

3. **SSL сертификат (опционально):**
   ```bash
   sudo apt-get install certbot python3-certbot-nginx
   sudo certbot --nginx -d dubaigemmsgifts.sbs
   ```

### 7. Мониторинг

```bash
# Статус сервисов
sudo systemctl status nginx
sudo systemctl status bottgpanel  # если создали service

# Логи
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Процессы
ps aux | grep python
ps aux | grep nginx
```

### 8. Docker (альтернативный подход)

Если используете Docker:

```bash
# Убедитесь, что порты правильно прокинуты
docker-compose up -d

# Проверьте логи
docker-compose logs -f

# Если нужно войти в контейнер
docker exec -it bottgpanel bash
```

## Итоговая структура

```
Клиент (браузер)
    ↓
Nginx (порт 80) - reverse proxy
    ↓
Flask (порт 5000) - веб-приложение
    ↓
Telegram Bot - обработка сообщений
```

## Контрольный список

- [ ] Flask запущен на `0.0.0.0:5000`
- [ ] Nginx установлен и запущен на порту 80
- [ ] Конфигурация Nginx указывает на `http://127.0.0.1:5000`
- [ ] Firewall открывает порты 80 и 5000 (если используется)
- [ ] `curl http://localhost:5000` возвращает корректный ответ
- [ ] `curl http://localhost:80` возвращает корректный ответ
- [ ] Логи Nginx не показывают ошибок
