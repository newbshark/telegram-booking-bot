import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import json

def fetch_habr():
    url = "https://freelance.habr.com/tasks.rss"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    items = []
    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            root = ET.fromstring(resp.read())
            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                desc = item.find("description").text if item.find("description") is not None else ""
                clean_desc = BeautifulSoup(desc, "html.parser").get_text().strip().replace("\n", " ")
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                items.append({
                    "source": "Хабр Фриланс",
                    "title": title,
                    "link": link,
                    "desc": clean_desc,
                    "date": pub_date
                })
    except Exception as e:
        print(f"Habr error: {e}")
    return items

def fetch_tg_posts(channel):
    url = f"https://t.me/s/{channel}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"})
    items = []
    try:
        with urllib.request.urlopen(req, timeout=7) as resp:
            soup = BeautifulSoup(resp.read(), "html.parser")
            msgs = soup.find_all("div", class_="tgme_widget_message")
            for m in msgs:
                text_node = m.find("div", class_="tgme_widget_message_text")
                link_node = m.find("a", class_="tgme_widget_message_date")
                if not text_node or not link_node:
                    continue
                text = text_node.get_text(separator=" ").strip()
                link = link_node.get("href", "")
                items.append({
                    "source": f"Telegram @{channel}",
                    "title": text[:70].replace("\n", " "),
                    "link": link,
                    "desc": text,
                    "date": "Сегодня"
                })
    except Exception as e:
        print(f"TG error {channel}: {e}")
    return items

if __name__ == "__main__":
    all_jobs = []
    all_jobs.extend(fetch_habr())
    all_jobs.extend(fetch_tg_posts("freelance_zakaz"))
    all_jobs.extend(fetch_tg_posts("freelance_feed"))
    
    print(f"Total jobs fetched: {len(all_jobs)}")
    
    # Ищем быстрые задачи по ботам, парсерам, скриптам, простым сайтам
    fast_jobs = []
    keywords = ["бот", "парс", "excel", "скрипт", "сайт", "лендинг", "python", "html", "таблиц", "сбор"]
    stop = ["битрикс", "bitrix", "1с", "1c", "wordpress", "fullstack", "senior", "lead", "дизайн", "рилс", "монтаж"]
    
    for job in all_jobs:
        text = (job["title"] + " " + job["desc"]).lower()
        if any(s in text for s in stop):
            continue
        if any(k in text for k in keywords):
            fast_jobs.append(job)
            
    print(f"Matching candidate jobs: {len(fast_jobs)}")
    for i, j in enumerate(fast_jobs[:10], 1):
        print("="*60)
        print(f"[{i}] {j['title']} ({j['source']})")
        print(f"URL: {j['link']}")
        print(f"DESC: {j['desc'][:300]}...")
