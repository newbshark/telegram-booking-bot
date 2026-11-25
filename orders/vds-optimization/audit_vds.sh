#!/bin/bash
# Экспресс-аудит VDS сервера: нагрузка, память, веб-сервер, php-fpm
echo "=========================================="
echo "         ЭКСПРЕСС-АУДИТ СЕРВЕРА VDS       "
echo "=========================================="
date
echo ""

echo "--- 1. ОС И ЯДРО ---"
uname -a
[ -f /etc/os-release ] && cat /etc/os-release | grep PRETTY_NAME
echo ""

echo "--- 2. ОПЕРАТИВНАЯ ПАМЯТЬ И SWAP ---"
free -h
echo ""

echo "--- 3. НАГРУЗКА НА ДИСК ---"
df -h /
echo ""

echo "--- 4. ПРОЦЕССОР И LOAD AVERAGE ---"
uptime
echo ""

echo "--- 5. ТОП-5 ПРОЦЕССОВ ПО ПАМЯТИ (RAM) ---"
ps aux --sort=-%mem | head -n 6
echo ""

echo "--- 6. СТАТУС ВЕБ-СЕРВЕРОВ И PHP ---"
echo "[*] Nginx:"
systemctl is-active nginx 2>/dev/null || echo "Не активен или не установлен"
echo "[*] Apache:"
systemctl is-active apache2 2>/dev/null || systemctl is-active httpd 2>/dev/null || echo "Не активен"
echo "[*] PHP-FPM процессы:"
ps aux | grep -E "php-fpm" | grep -v grep | wc -l | awk '{print "Всего воркеров PHP-FPM: " $1}'
echo ""

echo "--- 7. ПОСЛЕДНИЕ СРАБАТЫВАНИЯ OOM-KILLER (ЕСЛИ СЕРВЕР ПАДАЛ ИЗ-ЗА ПАМЯТИ) ---"
dmesg -T | grep -i -E "oom[- ]killer|out of memory" | tail -n 5 || echo "Срабатываний OOM-killer не обнаружено в dmesg"
echo "=========================================="
