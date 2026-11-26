#!/usr/bin/env python3
import os
import sys
import json
import time
import asyncio
import logging
import subprocess
import aiohttp
import html
import socket
from datetime import datetime
from dotenv import load_dotenv

import scanner

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_leads.json")

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
RADAR_CHANNEL_ID = os.getenv("RADAR_CHANNEL_ID")

if not BOT_TOKEN:
    logging.error("BOT_TOKEN не установлен в окружении или .env!")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_set), f, ensure_ascii=False, indent=2)

def send_desktop_notification(title, message):
    try:
        subprocess.run(["notify-send", "-a", "Tutor Radar", "-u", "normal", "-t", "6000", title, message], check=False)
    except Exception as e:
        logging.error(f"Ошибка notify-send: {e}")

async def send_telegram_alert(lead: dict):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    
    lead_text = lead["text"]
    if len(lead_text) > 450:
        lead_text = lead_text[:450] + "..."
    
    author_str = f"@{lead['author']}" if lead.get("author") else "В тексте сообщения / по ссылке"
    
    msg = (
        f"🎯 <b>РАДАР НАШЕЛ ЦЕЛЕВОГО КЛИЕНТА!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷️ <b>Категория:</b> {lead['category_title']}\n"
        f"📍 <b>Источник:</b> {lead.get('channel', 'Telegram')}\n\n"
        f"📝 <b>Текст запроса:</b>\n"
        f"<i>{html.escape(lead_text)}</i>\n\n"
        f"🔗 <b>Ссылка на заказ:</b> {lead['link']}\n"
        f"👤 <b>Контакт:</b> {author_str}\n\n"
        f"💬 <b>Готовый быстрый отклик (нажмите, чтобы скопировать):</b>\n"
        f"<code>{html.escape(lead['pitch'])}</code>"
    )

    target_chat = RADAR_CHANNEL_ID if RADAR_CHANNEL_ID else ADMIN_ID
    payload = {
        "chat_id": target_chat,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }

    conn = aiohttp.TCPConnector(family=socket.AF_INET)
    async with aiohttp.ClientSession(connector=conn) as session:
        try:
            async with session.post(url, json=payload, timeout=10) as resp:
                if resp.status != 200:
                    logging.error(f"Ошибка отправки Telegram алерта: {resp.status} - {await resp.text()}")
                    return False
                return True
        except Exception as e:
            logging.error(f"Исключение при отправке Telegram алерта: {e}")
            return False

async def run_radar():
    logging.info("🚀 [TUTOR RADAR] Радар учеников и школьных проектов успешно запущен!")
    seen = load_seen()
    logging.info(f"[*] Загружено ранее просмотренных заявок: {len(seen)}")

    while True:
        try:
            logging.info("[*] Сканирование каналов репетиторов, бирж и школьных проектов...")
            leads = await scanner.scan_all()
            new_leads_count = 0

            for lead in leads:
                # Уникальный ключ по тексту и ссылке
                lead_key = f"{lead['link']}_{hash(lead['text'][:100])}"
                if lead_key in seen:
                    continue

                seen.add(lead_key)
                new_leads_count += 1
                save_seen(seen)

                logging.info(f"🔥 НАЙДЕНА ЦЕЛЕВАЯ ЗАЯВКА: {lead['category_title']} ({lead.get('channel')})")
                
                # Десктоп уведомление
                send_desktop_notification(
                    f"🎯 Найдена заявка: {lead['category_title']}",
                    f"Источник: {lead.get('channel')}\n{lead['text'][:100]}..."
                )

                # Telegram уведомление с готовым откликом
                await send_telegram_alert(lead)
                await asyncio.sleep(1.5)

            logging.info(f"[*] Цикл завершен. Найдено новых: {new_leads_count}. Всего в базе: {len(seen)}")

        except Exception as e:
            logging.error(f"Ошибка в цикле сканирования: {e}")

        # Пауза 3 минуты между циклами (оптимально для отсутствия rate limits)
        await asyncio.sleep(180)

if __name__ == "__main__":
    asyncio.run(run_radar())
