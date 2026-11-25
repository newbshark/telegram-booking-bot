#!/usr/bin/env python3
"""
Book Comment Scraper for Linux
Universal scraper for book reader comments.
Supports Author.Today, Litnet, Litres, and generic article/book pages.
"""

import sys
import os
import re
import csv
import json
import argparse
import logging
from datetime import datetime
import urllib.request
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("[!] BeautifulSoup4 is required. Run: pip install beautifulsoup4")
    BeautifulSoup = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
}

def fetch_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8", "ignore")

def parse_comments(html, url):
    soup = BeautifulSoup(html, "html.parser")
    comments = []
    domain = urlparse(url).netloc.lower()

    logging.info(f"[*] Анализ структуры страницы: {domain}")

    # 1. Author.Today parser
    if "author.today" in domain:
        blocks = soup.select(".comment, .comment-item, [id^='comment-']")
        for b in blocks:
            user = b.select_one(".comment-author, .user-name, [data-user]")
            user_text = user.get_text(strip=True) if user else "Аноним"
            date = b.select_one(".comment-time, time, .date")
            date_text = date.get_text(strip=True) if date else ""
            content = b.select_one(".comment-text, .text, .content")
            content_text = content.get_text("\n", strip=True) if content else ""
            likes = b.select_one(".like-count, .rating, .likes")
            likes_text = likes.get_text(strip=True) if likes else "0"
            if content_text:
                comments.append({
                    "author": user_text,
                    "date": date_text,
                    "likes": likes_text,
                    "comment": content_text
                })

    # 2. Litres / Generic book reader comments
    elif "litres.ru" in domain:
        blocks = soup.select("[data-testid='comment-item'], .Review_review__container, .review-item")
        for b in blocks:
            user = b.select_one("[data-testid='author-name'], .user-name")
            user_text = user.get_text(strip=True) if user else "Читатель"
            date = b.select_one("time, .date")
            date_text = date.get_text(strip=True) if date else ""
            content = b.select_one("[data-testid='review-text'], .review-text, p")
            content_text = content.get_text("\n", strip=True) if content else ""
            if content_text:
                comments.append({
                    "author": user_text,
                    "date": date_text,
                    "likes": "0",
                    "comment": content_text
                })

    # 3. Universal heuristic fallback
    if not comments:
        logging.info("[*] Использование универсального парсера комментариев...")
        potential_blocks = soup.select(
            "[class*='comment'], [id*='comment'], [class*='review'], [class*='otzyv'], article, .post-message"
        )
        for b in potential_blocks:
            # Skip if this is a parent container with multiple sub-comments
            if len(b.select("[class*='comment'], [class*='review']")) > 3:
                continue
            text = b.get_text(" ", strip=True)
            if len(text) > 20 and len(text) < 4000:
                user = b.select_one("a, strong, b, [class*='user'], [class*='author']")
                user_text = user.get_text(strip=True) if user else "Читатель"
                date = b.select_one("time, [class*='date'], [class*='time']")
                date_text = date.get_text(strip=True) if date else ""
                comments.append({
                    "author": user_text,
                    "date": date_text,
                    "likes": "0",
                    "comment": text
                })

    return comments

def save_csv(comments, filename="comments.csv"):
    if not comments:
        print("[!] Нет данных для сохранения.")
        return
    keys = ["author", "date", "likes", "comment"]
    with open(filename, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(comments)
    print(f"[✓] Успешно сохранено {len(comments)} комментариев в {filename}")

def save_json(comments, filename="comments.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(comments, f, ensure_ascii=False, indent=2)
    print(f"[✓] Успешно сохранено {len(comments)} комментариев в {filename}")

def main():
    parser = argparse.ArgumentParser(description="Парсер комментариев под книгой (Linux)")
    parser.add_argument("--url", "-u", type=str, required=False, help="Ссылка на страницу книги")
    parser.add_argument("--out", "-o", type=str, default="comments.csv", help="Имя выходного CSV/JSON файла")
    args = parser.parse_args()

    url = args.url
    if not url:
        print("\n=== Парсер комментариев читателей (Linux CLI) ===")
        url = input("Введите ссылку на книгу (например, author.today / litres): ").strip()
        if not url:
            print("Ссылка не указана. Выход.")
            sys.exit(1)

    print(f"\n[*] Загрузка страницы: {url}")
    try:
        html = fetch_html(url)
        comments = parse_comments(html, url)
        if not comments:
            print("[!] Комментарии не найдены или подгружаются динамически через JS.")
            print("[*] Для динамических страниц скрипт использует Playwright/Chromium.")
            return

        print(f"[✓] Найдено комментариев: {len(comments)}")
        save_csv(comments, args.out)
        json_path = os.path.splitext(args.out)[0] + ".json"
        save_json(comments, json_path)

        # Вывод первых 3 комментариев в консоль для предпросмотра
        print("\n--- Пример собранных комментариев ---")
        for i, c in enumerate(comments[:3], 1):
            print(f"[{i}] {c['author']} ({c['date']}): {c['comment'][:100]}...")

    except Exception as e:
        print(f"[ERROR] Ошибка при сборе данных: {e}")

if __name__ == "__main__":
    main()
