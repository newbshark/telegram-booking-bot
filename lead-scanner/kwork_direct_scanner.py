#!/usr/bin/env python3
import os
import re
import json
import sqlite3
import shutil
import urllib.request
from bs4 import BeautifulSoup

def get_firefox_cookies_path():
    custom = os.getenv("FIREFOX_COOKIES_PATH")
    if custom and os.path.exists(custom):
        return custom
    home = os.path.expanduser("~")
    for base in [os.path.join(home, ".config", "mozilla", "firefox"), os.path.join(home, ".mozilla", "firefox")]:
        if os.path.exists(base):
            for entry in os.listdir(base):
                if "default" in entry:
                    cand = os.path.join(base, entry, "cookies.sqlite")
                    if os.path.exists(cand):
                        return cand
    return ""

TEMP_COOKIES_PATH = "/tmp/kwork_scanner_cookies.sqlite"

def get_kwork_cookies():
    cookie_path = get_firefox_cookies_path()
    if not cookie_path or not os.path.exists(cookie_path):
        return ""
    shutil.copyfile(cookie_path, TEMP_COOKIES_PATH)
    conn = sqlite3.connect(TEMP_COOKIES_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%kwork%'")
    cookies = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return "; ".join([f"{k}={v}" for k, v in cookies.items()])

def fetch_kwork_category(category_id=41): # 41: Скрипты и боты, 37: Сайты
    cookie_str = get_kwork_cookies()
    if not cookie_str:
        print("[!] Не удалось загрузить куки из браузера.")
        return []

    url = f"https://kwork.ru/projects?c={category_id}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
        "Cookie": cookie_str,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    })

    projects = []
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8")
            
            # Ищем блок wantsListData в HTML
            # В Kwork данные хранятся в window.stateData или в HTML структуре
            match = re.search(r'wantsListData\s*:\s*(\{.*?\})\s*,\s*"[a-zA-Z]', html)
            if match:
                try:
                    data = json.loads(match.group(1))
                    wants = data.get("wants", [])
                    for w in wants:
                        pid = w.get("id")
                        title = w.get("title", "")
                        desc = w.get("description", "").replace("\r\n", " ").replace("\n", " ")
                        price = w.get("priceLimit", 0)
                        offers_count = w.get("offers_count", 0)
                        time_left = w.get("timeLeft", "")
                        projects.append({
                            "id": pid,
                            "title": title,
                            "desc": desc,
                            "price": price,
                            "offers": offers_count,
                            "time_left": time_left,
                            "url": f"https://kwork.ru/projects/{pid}/view"
                        })
                except Exception as e:
                    print("JSON parse error:", e)
                    
            # Запасной парсинг регулярками, если JSON формат другой
            if not projects:
                pattern = re.compile(r'"id":(\d+).*?"title":"([^"]+)".*?"priceLimit":(\d+).*?"description":"([^"]+)"')
                for m in pattern.finditer(html):
                    pid, title, price, desc = m.groups()
                    desc_clean = desc.replace(r"\n", " ").replace(r"\r", "")
                    projects.append({
                        "id": pid,
                        "title": title,
                        "desc": desc_clean,
                        "price": price,
                        "offers": "?",
                        "time_left": "",
                        "url": f"https://kwork.ru/projects/{pid}/view"
                    })
    except Exception as e:
        print(f"Ошибка запроса Kwork (c={category_id}): {e}")
        
    return projects

if __name__ == "__main__":
    print("🔍 Парсинг проектов напрямую из вашего аккаунта Kwork...")
    bots_projects = fetch_kwork_category(41) # Скрипты и боты
    sites_projects = fetch_kwork_category(37) # Сайты
    
    all_projects = bots_projects + sites_projects
    print(f"✅ Найдено свежих проектов на Бирже: {len(all_projects)}\n")
    
    for i, p in enumerate(all_projects[:10], 1):
        print("="*65)
        print(f"[{i}] {p['title']} — Бюджет: {p['price']} ₽ (Откликов: {p['offers']})")
        print(f"🔗 {p['url']}")
        print(f"📝 {p['desc'][:200]}...")
