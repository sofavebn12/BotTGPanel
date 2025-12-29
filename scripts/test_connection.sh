#!/bin/bash
# Скрипт для проверки соединения Flask и Nginx

echo "=========================================="
echo "Проверка соединения Flask <-> Nginx"
echo "=========================================="
echo ""

# Проверяем, запущен ли Flask
echo "1. Проверка Flask (порт 5000)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 > /dev/null 2>&1; then
    echo "✅ Flask запущен на порту 5000"
    echo "   Статус код: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:5000)"
else
    echo "❌ Flask НЕ отвечает на порту 5000"
    echo "   Запустите Flask: python run.py или python start.py"
fi
echo ""

# Проверяем, запущен ли Nginx
echo "2. Проверка Nginx (порт 80)..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80 > /dev/null 2>&1; then
    echo "✅ Nginx запущен на порту 80"
    echo "   Статус код: $(curl -s -o /dev/null -w '%{http_code}' http://localhost:80)"
else
    echo "❌ Nginx НЕ отвечает на порту 80"
    echo "   Проверьте статус: sudo systemctl status nginx"
    echo "   Или запустите: sudo python start.py"
fi
echo ""

# Проверяем конфигурацию Nginx
echo "3. Проверка конфигурации Nginx..."
if command -v nginx &> /dev/null; then
    if sudo nginx -t &> /dev/null; then
        echo "✅ Конфигурация Nginx корректна"
    else
        echo "❌ Ошибка в конфигурации Nginx:"
        sudo nginx -t
    fi
else
    echo "⚠️  Nginx не установлен"
fi
echo ""

# Проверяем прослушиваемые порты
echo "4. Процессы, слушающие порты 80 и 5000..."
echo "Порт 5000 (Flask):"
sudo lsof -i :5000 2>/dev/null || echo "   Ничего не слушает порт 5000"
echo ""
echo "Порт 80 (Nginx):"
sudo lsof -i :80 2>/dev/null || echo "   Ничего не слушает порт 80"
echo ""

# Проверяем проксирование
echo "5. Тест проксирования через Nginx..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:80 > /dev/null 2>&1; then
    response=$(curl -s http://localhost:80)
    if [ ! -z "$response" ]; then
        echo "✅ Nginx успешно проксирует запросы на Flask"
    else
        echo "⚠️  Nginx отвечает, но содержимое пустое"
    fi
else
    echo "❌ Проксирование не работает"
fi
echo ""

echo "=========================================="
echo "Рекомендации:"
echo "=========================================="
echo "1. Если Flask не запущен:"
echo "   python run.py"
echo ""
echo "2. Если Nginx не запущен:"
echo "   sudo systemctl start nginx"
echo "   # или"
echo "   sudo python start.py"
echo ""
echo "3. Если нужно перезагрузить Nginx:"
echo "   sudo systemctl reload nginx"
echo ""
echo "4. Если Nginx не установлен:"
echo "   sudo apt-get install nginx"
echo ""
echo "5. Если порт 80 занят:"
echo "   sudo lsof -i :80"
echo "   sudo kill <PID>"
echo ""
