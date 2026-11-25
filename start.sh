#!/usr/bin/env bash
# Единый центр управления фриланс-хабом
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="$BASE_DIR/venv/bin/python"

clear
echo "=========================================================="
echo "          🚀 FREELANCE LAUNCHPAD / HUB                   "
echo "=========================================================="
echo "1) 🤖 Запустить ДЕМО-БОТА (Онлайн-запись и заявки)"
echo "2) 📡 Сканировать открытые Telegram-биржи на новые заказы"
echo "3) 🔍 Проанализировать текст любого заказа и сгенерировать отклик"
echo "4) 📄 Показать готовые тексты для Kwork и Авито"
echo "5) 🚪 Выход"
echo "=========================================================="
read -p "Выберите действие [1-5]: " choice

case $choice in
    1)
        if [ ! -f "$BASE_DIR/demo-bot/.env" ]; then
            echo ""
            echo "⚠️  Файл .env не найден в demo-bot/!"
            echo "Создайте бота через @BotFather в Telegram и укажите токен:"
            read -p "Введите токен бота (BOT_TOKEN): " token
            read -p "Введите ваш Telegram ID для заявок (ADMIN_ID): " admin_id
            echo "BOT_TOKEN=$token" > "$BASE_DIR/demo-bot/.env"
            echo "ADMIN_ID=$admin_id" >> "$BASE_DIR/demo-bot/.env"
            echo "✅ Файл .env успешно создан!"
        fi
        echo "Запуск бота..."
        cd "$BASE_DIR/demo-bot" && "$VENV_PYTHON" main.py
        ;;
    2)
        echo "Запуск сканера публичных каналов..."
        PYTHONPATH="$BASE_DIR/lead-scanner" "$VENV_PYTHON" "$BASE_DIR/lead-scanner/cli.py" scan
        ;;
    3)
        PYTHONPATH="$BASE_DIR/lead-scanner" "$VENV_PYTHON" "$BASE_DIR/lead-scanner/cli.py"
        ;;
    4)
        echo ""
        echo "Файлы с готовыми текстами объявлений:"
        echo "  - $BASE_DIR/gigs/kwork_telegram_bot.md"
        echo "  - $BASE_DIR/gigs/kwork_parser.md"
        echo "  - $BASE_DIR/gigs/avito_telegram_bot.md"
        echo "  - $BASE_DIR/portfolio/showcase_instructions.md"
        echo ""
        read -p "Нажмите Enter для возврата в меню..." dummy
        exec "$0"
        ;;
    5)
        echo "До встречи!"
        exit 0
        ;;
    *)
        echo "Неверный выбор."
        exit 1
        ;;
esac
