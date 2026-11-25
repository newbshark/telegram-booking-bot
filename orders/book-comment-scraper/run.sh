#!/bin/bash
# Запуск скрипта в 1 команду под Linux
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ ! -d "venv" ]; then
    echo "[*] Создание виртуального окружения Python..."
    python3 -m venv venv
    venv/bin/pip install --upgrade pip -q
    venv/bin/pip install beautifulsoup4 -q
    echo "[✓] Окружение готово!"
fi

venv/bin/python scraper.py "$@"
