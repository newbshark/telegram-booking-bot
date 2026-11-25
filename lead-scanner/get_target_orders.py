#!/usr/bin/env python3
import urllib.request
import re
import json
from bs4 import BeautifulSoup
from find_next_best import get_cookies, clean_unicode

cookies_dict = get_cookies()
cookie_str = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Cookie": cookie_str
}

def get_project_full(pid):
    url = f"https://kwork.ru/projects/{pid}/view"
    try:
        req = urllib.request.Request(url, headers=headers)
        html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", "ignore")
        
        soup = BeautifulSoup(html, "html.parser")
        title = soup.find("h1")
        title_text = title.get_text(strip=True) if title else "No title"
        
        # Price
        price_el = soup.find(class_=re.compile(r"price|bill|desired-price", re.I))
        price_text = price_el.get_text(strip=True) if price_el else ""
        
        # Offers count
        offers_text = ""
        for div in soup.find_all(["div", "span"]):
            t = div.get_text(strip=True)
            if "предложени" in t or "отклик" in t:
                if re.match(r"^\d+\s+(предложени|отклик)", t):
                    offers_text = t
                    break

        # Description
        desc_div = soup.find("div", class_="w-break") or soup.find("div", class_="project-description") or soup.find("div", class_="js-view-description")
        desc_text = desc_div.get_text(separator="\n", strip=True) if desc_div else ""
        if not desc_text:
            # try finding in raw text between markers
            m = re.search(r'\"description\":\"(.*?)\",\"(?:files|category_id|user_id)', html)
            if m:
                desc_text = clean_unicode(m.group(1).replace(r'\"', '"'))
        
        return {
            "id": pid,
            "title": title_text,
            "price": price_text,
            "offers": offers_text,
            "desc": desc_text,
            "url": url
        }
    except Exception as e:
        return {"id": pid, "error": str(e)}

if __name__ == "__main__":
    targets = [3275336, 3275354, 3275145, 3275058]
    for t in targets:
        info = get_project_full(t)
        print("="*60)
        print(f"ID: {info.get('id')} | {info.get('title')}")
        print(f"Цена: {info.get('price')} | Отклики: {info.get('offers')}")
        print(f"URL: {info.get('url')}")
        print(f"Описание:\n{info.get('desc')}")
        print()
