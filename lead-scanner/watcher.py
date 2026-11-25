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

from analyzer import analyze_job, PUBLIC_CHANNELS
import scanner_web

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HUB_DIR = os.path.dirname(BASE_DIR)
SEEN_FILE = os.path.join(BASE_DIR, "seen_leads.json")
ENV_FILE = os.path.join(HUB_DIR, "demo-bot", ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def get_env_config():
    bot_token = ""
    admin_id = 0
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as f:
            for line in f:
                if line.startswith("BOT_TOKEN="):
                    bot_token = line.strip().split("=", 1)[1]
                elif line.startswith("ADMIN_ID="):
                    try:
                        admin_id = int(line.strip().split("=", 1)[1])
                    except:
                        pass
    return bot_token, admin_id

def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_seen(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_set), f, ensure_ascii=False, indent=2)

def send_desktop_notification(title, message):
    try:
        subprocess.run(["notify-send", "-a", "Freelance Radar", "-u", "normal", "-t", "5000", title, message], check=False)
    except Exception as e:
        logging.error(f"Ошибка отправки notify-send: {e}")

async def send_telegram_alert(bot_token, admin_id, lead):
    if not bot_token or not admin_id:
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    contact_block = ""
    contact = lead.get("contact")
    if contact:
        contact_clean = contact.replace("@", "")
        contact_block = f"👤 <b>Заказчик:</b> @{html.escape(contact_clean)} (<a href=\"https://t.me/{contact_clean}\">Написать в ЛС</a>)\n"
    
    channel_title = lead['channel']
    if channel_title.startswith("kwork_proj_"):
        source_label = f"Биржа Kwork (ID: {channel_title.replace('kwork_proj_', '')})"
    else:
        source_label = f"@{channel_title}"

    text = (
        f"🔥 <b>НОВЫЙ ЗАКАЗ: {html.escape(lead['category'].upper())}</b>\n\n"
        f"📍 <b>Источник:</b> {html.escape(source_label)}\n"
        f"🔗 <a href=\"{lead['link']}\">Открыть заказ</a>\n"
        f"{contact_block}\n"
        f"📝 <b>Описание:</b>\n{html.escape(lead['text'][:350])}...\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"💬 <b>Готовый отклик (нажми, чтобы скопировать):</b>\n"
        f"<code>{html.escape(lead['proposal'])}</code>"
    )
    payload = {
        "chat_id": admin_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        conn = aiohttp.TCPConnector(family=socket.AF_INET, ssl=False)
        async with aiohttp.ClientSession(connector=conn) as session:
            async with session.post(url, json=payload, timeout=12) as resp:
                if resp.status != 200:
                    err_txt = await resp.text()
                    logging.error(f"Ошибка Telegram API ({resp.status}): {err_txt}")
                    return False
                return True
    except Exception as e:
        logging.error(f"Ошибка отправки алерта в Telegram: {e}")
        return False

async def run_radar_cycle():
    seen = load_seen()
    bot_token, admin_id = get_env_config()
    
    logging.info("[*] Сканирование каналов заказов...")
    leads = await scanner_web.scan_all_channels()
    
    new_count = 0
    for lead in leads:
        lead_id = lead.get("link") or lead.get("text")[:60]
        if lead_id not in seen:
            seen.add(lead_id)
            new_count += 1
            logging.info(f"[+] Новый подходящий заказ: {lead['category']} из @{lead['channel']}")
            
            # 1. Desktop Notification (Hyprland / Wayland)
            send_desktop_notification(
                f"🔥 Новый заказ: {lead['category'].upper()} (@{lead['channel']})",
                lead['text'][:120]
            )
            
            # 2. Telegram Alert
            if bot_token and admin_id:
                await send_telegram_alert(bot_token, admin_id, lead)
                await asyncio.sleep(0.6)
                
    save_seen(seen)
    logging.info(f"[*] Цикл завершен. Найдено новых: {new_count}. Всего в базе: {len(seen)}")

async def main_loop():
    logging.info("🚀 Фоновый радар заказов запущен! Периодичность: каждые 5 минут.")
    while True:
        try:
            await run_radar_cycle()
        except Exception as e:
            logging.error(f"Ошибка в цикле радара: {e}")
        await asyncio.sleep(300)

if __name__ == "__main__":
    asyncio.run(main_loop())
