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
    if not cookie_path or not os.path.exists(cookie_path):
        return {}
    shutil.copyfile(cookie_path, TEMP_COOKIES_PATH)
    conn = sqlite3.connect(TEMP_COOKIES_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, value FROM moz_cookies WHERE host LIKE '%kwork%'")
    cookies = {row[0]: row[1] for row in cursor.fetchall()}
    conn.close()
    return cookies

def clean_unicode(text):
    if not text:
        return ""
    try:
        return text.encode('latin1').decode('utf-8')
    except:
        try:
            return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
        except:
            return text

async def fetch_projects_category(session, cat_id=41):
    url = f"https://kwork.ru/projects?c={cat_id}"
    projects = []
    try:
        async with session.get(url) as resp:
            if resp.status != 200:
                return projects
            raw_bytes = await resp.read()
            html = raw_bytes.decode("utf-8", "ignore")
            
            for block in re.split(r'\{\"userAlreadyWork\"', html)[1:]:
                m_id = re.search(r'\"id\":(\d+)', block)
                m_price = re.search(r'\"possiblePriceLimit\":(\d+)', block)
                m_desc = re.search(r'\"description\":\"(.*?)\",\"(?:files|category_id|user_id)', block)
                m_date = re.search(r'\"dateCreate\":\"(.*?)\"', block)
                m_offers = re.search(r'\"kwork_count\":(\d+)', block)
                m_title = re.search(r'\"title\":\"(.*?)\"', block)
                
                if m_id and m_desc:
                    pid = m_id.group(1)
                    desc_raw = m_desc.group(1).replace(r'\"', '"')
                    desc = clean_unicode(desc_raw).replace("\r\n", " ").replace("\n", " ")
                    
                    price = m_price.group(1) if m_price else "500"
                    date_c = clean_unicode(m_date.group(1)) if m_date else "Сегодня"
                    offers = m_offers.group(1) if m_offers else "0"
                    
                    title = clean_unicode(m_title.group(1)) if m_title and "Сбор предложений" not in m_title.group(1) else desc[:70]
                    
                    projects.append({
                        "id": pid,
                        "title": title,
                        "desc": desc,
                        "price": price,
                        "date": date_c,
                        "offers": offers,
                        "url": f"https://kwork.ru/projects/{pid}/view"
                    })
    except Exception as e:
        print(f"Error category {cat_id}: {e}")
    return projects

async def main():
    cookies = get_cookies()
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    timeout = aiohttp.ClientTimeout(total=8)
    async with aiohttp.ClientSession(headers=headers, cookies=cookies, timeout=timeout) as session:
        bots = await fetch_projects_category(session, 41)
        sites = await fetch_projects_category(session, 37)
        
        all_p = bots + sites
        print(f"✅ Найдено проектов на Бирже Kwork: {len(all_p)}\n")
        
        # Сортируем: сначала сегодняшние
        all_p.sort(key=lambda x: "24 ноября" in x["date"], reverse=True)
        
        for i, p in enumerate(all_p[:6], 1):
            print("="*65)
            print(f"[{i}] {p['title']}")
            print(f"💰 Бюджет: {p['price']} ₽ | Дата: {p['date']} | Откликов: {p['offers']}")
            print(f"🔗 {p['url']}")
            print(f"📝 {p['desc'][:260]}...")

if __name__ == "__main__":
    asyncio.run(main())
