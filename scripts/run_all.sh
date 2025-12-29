#!/bin/bash
# Запуск всех сервисов (Flask + Bot + Nginx)

echo "🚀 Запуск всех сервисов (Flask + Bot + Nginx)..."
echo "⚠️  Требуется sudo для запуска Nginx на порту 80"
echo ""

cd "$(dirname "$0")/.."

# Проверка прав sudo
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Пожалуйста, запустите с sudo:"
    echo "   sudo ./scripts/run_all.sh"
    exit 1
fi

echo "✅ Запуск с правами root"
python start.py
