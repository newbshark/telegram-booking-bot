#!/usr/bin/env python3
import urllib.request
import json
import time
import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("[ERR] BOT_TOKEN не найден в окружении!")
    sys.exit(1)
ENV_FILE = "/home/void/Lessons/marketing/tutor-radar/.env"

print("Waiting for any post in the channel...")
start_time = time.time()
found_chat_id = None
chat_title = ""
offset = None

while time.time() - start_time < 300:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?allowed_updates=[\"channel_post\"]&timeout=5"
    if offset:
        url += f"&offset={offset}"
    try:
        req = urllib.request.urlopen(url, timeout=10)
        data = json.loads(req.read().decode())
        for update in data.get("result", []):
            offset = update["update_id"] + 1
            if "channel_post" in update:
                chat = update["channel_post"]["chat"]
                found_chat_id = chat["id"]
                chat_title = chat.get("title", "Радар")
                print(f"[OK] Обнаружен канал: {chat_title} (ID: {found_chat_id})")
                break
        if found_chat_id:
            break
    except Exception as e:
        print(f"Polling error: {e}")
    time.sleep(1)

if not found_chat_id:
    print("[TIMEOUT] Сообщение в канал не поступило за отведенное время.")
    sys.exit(1)

# Send welcome test alert directly to the channel
send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
welcome_msg = (
    "🎯 <b>РАДАР ЗАКАЗОВ IT УСПЕШНО ПОДКЛЮЧЕН!</b>\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "✅ Канал авторизован для приема горячих лидов.\n"
    "📡 <b>Мониторинг:</b> Unity 3D, C#, моддинг GTA 5, школьные проекты (ИИП).\n\n"
    "💡 <i>В основном боте @MyStudioBookingBot теперь будут оставаться исключительно твои личные клиенты и записи на уроки.</i>"
)

payload = json.dumps({
    "chat_id": found_chat_id,
    "text": welcome_msg,
    "parse_mode": "HTML"
}).encode("utf-8")

try:
    req = urllib.request.Request(send_url, data=payload, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req, timeout=10)
    print(f"[OK] Приветственное сообщение отправлено в канал {found_chat_id}!")
except Exception as e:
    print(f"[ERR] Ошибка отправки сообщения в канал: {e}")

# Save to .env
env_lines = []
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r") as f:
        for line in f:
            if not line.startswith("RADAR_CHANNEL_ID="):
                env_lines.append(line.strip())

env_lines.append(f"RADAR_CHANNEL_ID={found_chat_id}")
with open(ENV_FILE, "w") as f:
    f.write("\n".join(env_lines) + "\n")

print(f"[OK] RADAR_CHANNEL_ID={found_chat_id} сохранен в {ENV_FILE}")
