#!/usr/bin/env python3
import asyncio
import aiohttp
from find_next_best import get_cookies, fetch_category

async def show_all():
    cookies = get_cookies()
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"}
    async with aiohttp.ClientSession(headers=headers, cookies=cookies) as session:
        # 41: Скрипты и боты, 37: Сайты под ключ, 11: Верстка, 81: Доработка сайтов, 15: Парсинг данных
        tasks = [fetch_category(session, c) for c in [41, 37, 11, 81, 15]]
        res = await asyncio.gather(*tasks)
        seen = set()
        clean = []
        for cat_list in res:
            for p in cat_list:
                if p["id"] not in seen and p["id"] != "3275326":
                    seen.add(p["id"])
                    clean.append(p)
        clean.sort(key=lambda x: x["offers"])
        print(f"Total projects found: {len(clean)}")
        for p in clean:
            print("="*60)
            print(f"ID: {p['id']} | Цена: {p['price']} ₽ | Откликов: {p['offers']} | Дата: {p['date']}")
            print(f"URL: {p['url']}")
            print(f"Desc: {p['desc'][:300]}")

if __name__ == "__main__":
    asyncio.run(show_all())
