#!/bin/bash
# Защита VDS от падений (OOM Killer): настройка файла подкачки SWAP и лимитов
set -e

echo "[*] Проверка существующего SWAP..."
CURRENT_SWAP=$(free -m | awk '/Swap:/ {print $2}')

if [ "$CURRENT_SWAP" -lt 1024 ]; then
    echo "[*] На сервере мало или нет Swap ($CURRENT_SWAP MB). Создание 2GB файла подкачки..."
    fallocate -l 2G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=2048
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    
    # Добавляем в fstab для автозагрузки
    if ! grep -q "/swapfile" /etc/fstab; then
        echo "/swapfile none swap sw 0 0" >> /etc/fstab
    fi
    echo "[✓] SWAP 2GB успешно подключен!"
else
    echo "[✓] SWAP уже настроен ($CURRENT_SWAP MB)."
fi

# Оптимизация swappiness (сбрасывать в swap только при острой нехватке памяти)
echo "[*] Настройка vm.swappiness = 10..."
sysctl vm.swappiness=10
sysctl vm.vfs_cache_pressure=50

if ! grep -q "vm.swappiness" /etc/sysctl.conf; then
    echo "vm.swappiness=10" >> /etc/sysctl.conf
    echo "vm.vfs_cache_pressure=50" >> /etc/sysctl.conf
fi

echo "[✓] Защита от OOM падений активирована!"
