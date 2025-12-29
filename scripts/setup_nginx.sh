#!/bin/bash
# Настройка Nginx на хост-машине

echo "=========================================="
echo "Настройка Nginx для BotTGPanel"
echo "=========================================="
echo ""

# Проверка прав sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Требуются права sudo. Запустите:"
    echo "   sudo ./scripts/setup_nginx.sh"
    exit 1
fi

# Проверка установки Nginx
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx не установлен"
    echo "Установить Nginx? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        apt-get update
        apt-get install -y nginx
        echo "✅ Nginx установлен"
    else
        echo "Отменено"
        exit 1
    fi
fi

# Путь к конфигурации
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
NGINX_CONF="$PROJECT_DIR/nginx/conf.d/dubaigemmsgifts.sbs.conf"

echo ""
echo "📁 Проект: $PROJECT_DIR"
echo "📄 Конфигурация: $NGINX_CONF"
echo ""

# Проверка существования конфигурации
if [ ! -f "$NGINX_CONF" ]; then
    echo "❌ Конфигурация не найдена: $NGINX_CONF"
    exit 1
fi

# Копирование конфигурации
echo "📋 Копирование конфигурации..."
cp "$NGINX_CONF" /etc/nginx/sites-available/dubaigemmsgifts.sbs.conf

# Создание символической ссылки
echo "🔗 Создание символической ссылки..."
ln -sf /etc/nginx/sites-available/dubaigemmsgifts.sbs.conf /etc/nginx/sites-enabled/dubaigemmsgifts.sbs.conf

# Удаление дефолтной конфигурации (опционально)
if [ -f /etc/nginx/sites-enabled/default ]; then
    echo "🗑️  Удалить дефолтную конфигурацию Nginx? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        rm /etc/nginx/sites-enabled/default
        echo "✅ Дефолтная конфигурация удалена"
    fi
fi

# Проверка конфигурации
echo ""
echo "🔍 Проверка конфигурации Nginx..."
if nginx -t; then
    echo "✅ Конфигурация корректна"
else
    echo "❌ Ошибка в конфигурации!"
    exit 1
fi

# Перезагрузка Nginx
echo ""
echo "🔄 Перезагрузка Nginx..."
systemctl reload nginx

# Проверка статуса
echo ""
echo "📊 Статус Nginx:"
systemctl status nginx --no-pager

echo ""
echo "=========================================="
echo "✅ Настройка завершена!"
echo "=========================================="
echo ""
echo "Теперь запустите Flask:"
echo "  python run.py"
echo ""
echo "Или все сервисы:"
echo "  sudo python start.py"
echo ""
echo "Проверить соединение:"
echo "  ./scripts/test_connection.sh"
echo ""
