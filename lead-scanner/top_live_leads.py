#!/usr/bin/env python3
import urllib.request
import re
import json
from find_next_best import get_cookies, clean_unicode

cookies_dict = get_cookies()
cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0)", "Cookie": cookie_str}

all_p = []
seen = set()

for page in range(1, 10):
    url = f"https://kwork.ru/projects?page={page}"
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=8).read().decode("utf-8", "ignore")
        for block in re.split(r'\{\"userAlreadyWork\"', html)[1:]:
            m_id = re.search(r'\"id\":(\d+)', block)
            m_title = re.search(r'\"title\":\"(.*?)\"', block)
            m_desc = re.search(r'\"description\":\"(.*?)\",\"(?:files|category_id|user_id)', block)
            m_price = re.search(r'\"possiblePriceLimit\":(\d+)', block)
            m_offers = re.search(r'\"kwork_count\":(\d+)', block)
            m_date_act = re.search(r'\"dateActive\":\"(.*?)\"', block)
            m_date_cre = re.search(r'\"dateCreate\":\"(.*?)\"', block)
            m_cat = re.search(r'\"category_id\":(\d+)', block)
            
            if m_id and m_desc:
                pid = m_id.group(1)
                if pid in seen: continue
                seen.add(pid)
                
                title = clean_unicode(m_title.group(1)) if m_title else ""
                desc = clean_unicode(m_desc.group(1).replace(r'\"', '"')).replace("\r\n", " ").replace("\n", " ")
                price = int(m_price.group(1)) if m_price else 500
                offers = int(m_offers.group(1)) if m_offers else 0
                date_act = clean_unicode(m_date_act.group(1)) if m_date_act else ""
                date_cre = clean_unicode(m_date_cre.group(1)) if m_date_cre else ""
                cat = m_cat.group(1) if m_cat else ""
                
                all_p.append({
                    "id": pid, "title": title, "desc": desc, "price": price,
                    "offers": offers, "dateActive": date_act, "dateCreate": date_cre,
                    "cat": cat, "url": f"https://kwork.ru/projects/{pid}/view"
                })
    except Exception as e:
        print(f"Page {page} err: {e}")

print(f"Total projects fetched: {len(all_p)}")

# 1. 3D / Print / CAD
p_3d = [p for p in all_p if any(w in p["desc"].lower() or w in p["title"].lower() for w in ["3d", "модел", "печать", "скульпт", "stl", "step", "blender"])]

# 2. Python / Bots / API / Automation
p_py = [p for p in all_p if any(w in p["desc"].lower() or w in p["title"].lower() for w in ["бот", "bot", "python", "парс", "api", "ozon", "wb", "chatgpt", "скрипт", "интеграц", "автоматиз", "сервер", "vps"])]

# 3. Web / Dev
p_web = [p for p in all_p if any(w in p["desc"].lower() or w in p["title"].lower() for w in ["лендинг", "сайт", "верстк", "html", "css", "js", "тильд", "tilda"]) and not any(w in p["desc"].lower() for w in ["битрикс", "bitrix", "1с"])]

print("\n=== TOP 3D & HARDWARE ===")
for p in sorted(p_3d, key=lambda x: x["offers"])[:5]:
    print(f"[{p['offers']} откл.] {p['price']} ₽ | {p['title']} | ID: {p['id']} | {p['url']}")
    print(f"   {p['desc'][:180]}...")

print("\n=== TOP PYTHON / BOTS / AUTOMATION / API ===")
for p in sorted(p_py, key=lambda x: x["offers"])[:8]:
    print(f"[{p['offers']} откл.] {p['price']} ₽ | {p['title']} | ID: {p['id']} | {p['url']}")
    print(f"   {p['desc'][:180]}...")

print("\n=== TOP WEB / DEV ===")
for p in sorted(p_web, key=lambda x: x["offers"])[:5]:
    print(f"[{p['offers']} откл.] {p['price']} ₽ | {p['title']} | ID: {p['id']} | {p['url']}")
    print(f"   {p['desc'][:180]}...")
