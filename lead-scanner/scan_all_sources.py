#!/usr/bin/env python3
import urllib.request
import re
import json
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from find_next_best import get_cookies, clean_unicode

cookies_dict = get_cookies()
cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Cookie": cookie_str
}

def scan_habr():
    print("=== HABR FREELANCE ===")
    url = "https://freelance.habr.com/tasks.rss"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            root = ET.fromstring(r.read())
            items = root.findall(".//item")
            for item in items[:8]:
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                desc_text = BeautifulSoup(desc, "html.parser").get_text(separator=" ").strip()
                print(f"[*] {title} | {link}")
                print(f"    {desc_text[:200]}...")
    except Exception as e:
        print(f"Habr error: {e}")

def scan_tg(channel):
    print(f"=== TG @{channel} ===")
    url = f"https://t.me/s/{channel}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            soup = BeautifulSoup(r.read(), "html.parser")
            msgs = soup.find_all("div", class_="tgme_widget_message")
            count = 0
            for m in reversed(msgs):
                t_node = m.find("div", class_="tgme_widget_message_text")
                l_node = m.find("a", class_="tgme_widget_message_date")
                if not t_node: continue
                text = t_node.get_text(separator=" ").strip()
                link = l_node.get("href", "") if l_node else ""
                # Quick keyword filter
                lower = text.lower()
                keywords = ["бот", "bot", "парс", "python", "скрипт", "автоматиз", "3d", "печать", "api", "интеграц", "web", "разработ"]
                if any(k in lower for k in keywords):
                    print(f"[*] {link}")
                    print(f"    {text[:220].replace(chr(10), ' ')}...")
                    count += 1
                    if count >= 3: break
    except Exception as e:
        print(f"TG error {channel}: {e}")

if __name__ == "__main__":
    scan_habr()
    print()
    for ch in ["it_zakazy", "freelance_orders", "tg_bots_dev"]:
        scan_tg(ch)
        print()
