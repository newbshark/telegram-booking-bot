#!/usr/bin/env python3
import urllib.request
import re
import json
from find_next_best import get_cookies, clean_unicode

cookies_dict = get_cookies()
cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0", "Cookie": cookie_str}

seen = set()
all_projects = []

for page in [1, 2, 3, 4]:
    url = f"https://kwork.ru/projects?page={page}"
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=6).read().decode("utf-8", "ignore")
        for block in re.split(r'\{\"userAlreadyWork\"', html)[1:]:
            m_id = re.search(r'\"id\":(\d+)', block)
            m_desc = re.search(r'\"description\":\"(.*?)\",\"(?:files|category_id|user_id)', block)
            m_title = re.search(r'\"title\":\"(.*?)\"', block)
            m_price = re.search(r'\"possiblePriceLimit\":(\d+)', block)
            m_date = re.search(r'\"dateCreate\":\"(.*?)\"', block)
            m_offers = re.search(r'\"kwork_count\":(\d+)', block)
            if m_id and m_desc:
                pid = m_id.group(1)
                if pid in seen: continue
                seen.add(pid)
                title = clean_unicode(m_title.group(1)) if m_title else ""
                desc = clean_unicode(m_desc.group(1).replace(r'\"', '"')).replace("\r\n", " ").replace("\n", " ")
                price = int(m_price.group(1)) if m_price else 500
                date_c = clean_unicode(m_date.group(1)) if m_date else ""
                offers = int(m_offers.group(1)) if m_offers else 0
                
                if "24 ноября" in date_c or "23 ноября" in date_c:
                    all_projects.append({
                        "id": pid,
                        "title": title,
                        "desc": desc,
                        "price": price,
                        "date": date_c,
                        "offers": offers,
                        "url": f"https://kwork.ru/projects/{pid}/view"
                    })
    except Exception as e:
        pass

banned = ["битрикс", "bitrix", "1с", "1c", "видеомонтаж", "озвучк", "атол", "скульпт", "3d", "песню", "ролик", "комикс", "аватар", "налог", "анимационный", "дорам", "фанфик"]
clean = [p for p in all_projects if not any(w in p["desc"].lower() for w in banned) and p["id"] not in ["3275326", "3275337", "3275312", "3275209"]]
clean.sort(key=lambda x: x["offers"])

print(f"Total fresh clean projects: {len(clean)}")
for p in clean[:15]:
    print("="*65)
    print(f"ID: {p['id']} | Бюджет: {p['price']} ₽ | Откликов: {p['offers']} | Дата: {p['date']}")
    print(f"URL: {p['url']}")
    print(f"Desc: {p['desc'][:260]}")
