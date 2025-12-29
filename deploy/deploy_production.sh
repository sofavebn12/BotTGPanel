#!/bin/bash
# Скрипт для развертывания в production

set -e  # Остановить при ошибке

echo "=========================================="
echo "Production Deployment - BotTGPanel"
echo "=========================================="
echo ""

# Проверка прав sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Требуются права sudo. Запустите:"
    echo "   sudo ./deploy/deploy_production.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Директория проекта: $PROJECT_DIR"
echo ""

# Шаг 1: Установка зависимостей системы
echo "1️⃣ Установка системных зависимостей..."
apt-get update
apt-get install -y python3-pip python3-venv nginx

# Шаг 2: Создание виртуального окружения
echo ""
echo "2️⃣ Создание виртуального окружения..."
cd "$PROJECT_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Виртуальное окружение создано"
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Шаг 3: Установка Python зависимостей
echo ""
echo "3️⃣ Установка Python зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # Production WSGI server
deactivate

# Шаг 4: Настройка Nginx
echo ""
echo "4️⃣ Настройка Nginx..."
cp "$PROJECT_DIR/nginx/conf.d/dubaigemmsgifts.sbs.conf" /etc/nginx/sites-available/bottgpanel.conf
ln -sf /etc/nginx/sites-available/bottgpanel.conf /etc/nginx/sites-enabled/bottgpanel.conf

# Удаление дефолтной конфигурации
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Проверка конфигурации Nginx
nginx -t

# Шаг 5: Настройка systemd service
echo ""
echo "5️⃣ Настройка systemd service..."

# Создание пользователя для сервиса (если не существует)
if ! id "bottgpanel" &>/dev/null; then
    useradd -r -s /bin/false bottgpanel
    echo "✅ Пользователь bottgpanel создан"
fi

# Копирование service файла
cp "$PROJECT_DIR/deploy/bottgpanel.service" /etc/systemd/system/

# Обновление путей в service файле
sed -i "s|/workspaces/BotTGPanel|$PROJECT_DIR|g" /etc/systemd/system/bottgpanel.service

# Настройка прав доступа
chown -R bottgpanel:bottgpanel "$PROJECT_DIR"
chmod -R 755 "$PROJECT_DIR"

# Шаг 6: Настройка firewall
echo ""
echo "6️⃣ Настройка firewall..."
if command -v ufw &> /dev/null; then
    ufw allow 80/tcp
    ufw allow 443/tcp
    echo "✅ Firewall настроен"
else
    echo "⚠️  UFW не установлен, пропускаем настройку firewall"
fi

# Шаг 7: Запуск сервисов
echo ""
echo "7️⃣ Запуск сервисов..."

# Перезагрузка systemd
systemctl daemon-reload

# Включение автозапуска
systemctl enable bottgpanel
systemctl enable nginx

# Запуск сервисов
systemctl restart bottgpanel
systemctl restart nginx

# Проверка статуса
sleep 2
systemctl status bottgpanel --no-pager
systemctl status nginx --no-pager

echo ""
echo "=========================================="
echo "✅ Развертывание завершено!"
echo "=========================================="
echo ""
echo "Сервисы:"
echo "  Flask (Gunicorn): http://localhost:5000"
echo "  Nginx:            http://localhost:80"
echo ""
echo "Управление сервисами:"
echo "  sudo systemctl start bottgpanel"
echo "  sudo systemctl stop bottgpanel"
echo "  sudo systemctl restart bottgpanel"
echo "  sudo systemctl status bottgpanel"
echo ""
echo "Логи:"
echo "  sudo journalctl -u bottgpanel -f"
echo "  sudo tail -f /var/log/nginx/access.log"
echo "  sudo tail -f /var/log/nginx/error.log"
echo ""
