#!/usr/bin/env python3
import os
import re
import json
import sqlite3
import shutil
import aiohttp
import asyncio

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

TEMP_COOKIES_PATH = "/tmp/kwork_ff_cookies.sqlite"

def get_cookies():
    cookie_path = get_firefox_cookies_path()
    if not cookie_path or not os.path.exists(cookie_path): return {}
    shutil.copyfile(cookie_path, TEMP_COOKIES_PATH)
    conn = sqlite3.connect(TEMP_COOKIES_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%kwork%'")
    cookies = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return cookies

def clean_unicode(text):
    if not text: return ""
    try: return text.encode("latin1").decode("utf-8")
    except: return text

async def fetch_category(session, cat_id):
    url = f"https://kwork.ru/projects?c={cat_id}"
    projects = []
    try:
        async with session.get(url) as resp:
            if resp.status != 200: return []
            html = (await resp.read()).decode("utf-8", "ignore")
            for block in re.split(r'\{\"userAlreadyWork\"', html)[1:]:
                m_id = re.search(r'\"id\":(\d+)', block)
                m_price = re.search(r'\"possiblePriceLimit\":(\d+)', block)
                m_desc = re.search(r'\"description\":\"(.*?)\",\"(?:files|category_id|user_id)', block)
                m_date = re.search(r'\"dateCreate\":\"(.*?)\"', block)
                m_offers = re.search(r'\"kwork_count\":(\d+)', block)
                
                if m_id and m_desc:
                    pid = m_id.group(1)
                    desc = clean_unicode(m_desc.group(1).replace(r'\"', '"')).replace("\r\n", " ").replace("\n", " ")
                    price = m_price.group(1) if m_price else "500"
                    date_c = clean_unicode(m_date.group(1)) if m_date else "Сегодня"
                    offers = m_offers.group(1) if m_offers else "0"
                    
                    if "24 ноября" in date_c:
                        projects.append({
                            "id": pid,
                            "price": int(price) if str(price).isdigit() else 500,
                            "date": date_c,
                            "offers": int(offers) if str(offers).isdigit() else 0,
                            "desc": desc,
                            "url": f"https://kwork.ru/projects/{pid}/view"
                        })
    except Exception as e:
        pass
    return projects

async def main():
    cookies = get_cookies()
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"}
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as session:
        tasks = [fetch_category(session, 41), fetch_category(session, 37), fetch_category(session, 11)]
        res = await asyncio.gather(*tasks)
        
        seen = set()
        clean = []
        for cat_list in res:
            for p in cat_list:
                if p["id"] not in seen and p["id"] != "3275326": # исключаем уже отправленный заказ
                    seen.add(p["id"])
                    low = p["desc"].lower()
                    # Убираем нерелевантные темы
                    if not any(s in low for s in ["gmail", "битрикс", "bitrix", "1с", "1c", "wordpress", "ролик", "видео"]):
                        clean.append(p)
                        
        print(f"Total unique target jobs today: {len(clean)}")
        for i, p in enumerate(clean[:6], 1):
            pid = p["id"]
            price = p["price"]
            offers = p["offers"]
            desc = p["desc"][:260]
            url = p["url"]
            print("="*65)
            print(f"[{i}] Проект #{pid} | Бюджет: {price} ₽ | Откликов: {offers}")
            print(f"🔗 {url}")
            print(f"📝 {desc}...")

if __name__ == "__main__":
    asyncio.run(main())
