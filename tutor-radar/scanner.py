#!/usr/bin/env python3
import re
import json
import asyncio
import aiohttp
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from analyzer import CHANNELS, analyze_lead

async def fetch_channel_posts(session: aiohttp.ClientSession, channel: str) -> List[Dict[str, Any]]:
    url = f"https://t.me/s/{channel}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    posts = []
    try:
        async with session.get(url, headers=headers, timeout=8) as resp:
            if resp.status != 200:
                return posts
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            message_nodes = soup.find_all("div", class_="tgme_widget_message")
            for node in message_nodes:
                text_node = node.find("div", class_="tgme_widget_message_text")
                link_node = node.find("a", class_="tgme_widget_message_date")
                if not text_node or not link_node:
                    continue
                
                text = text_node.get_text(separator="\n").strip()
                link = link_node.get("href", "")
                
                lead = analyze_lead(text)
                if lead:
                    lead["channel"] = f"Telegram @{channel}"
                    lead["link"] = link
                    posts.append(lead)
    except Exception:
        pass
    return posts

async def fetch_fl_feed(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Парсинг официального RSS-фида FL.ru (крупнейшая биржа РФ)"""
    url = "https://www.fl.ru/rss/all.xml"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    posts = []
    try:
        async with session.get(url, headers=headers, timeout=8) as resp:
            if resp.status != 200:
                return posts
            xml_text = await resp.text()
            root = ET.fromstring(xml_text)
            for it in root.findall(".//item"):
                t = it.find("title").text if it.find("title") is not None else ""
                d = it.find("description").text if it.find("description") is not None else ""
                link = it.find("link").text if it.find("link") is not None else ""
                
                # Чистим HTML тэги из описания
                clean_desc = re.sub(r"<[^>]+>", " ", d).strip()
                full_text = f"{t}\n\n{clean_desc}"
                
                lead = analyze_lead(full_text)
                if lead:
                    lead["channel"] = "FL.ru"
                    lead["link"] = link
                    posts.append(lead)
    except Exception:
        pass
    return posts

async def fetch_freelancehunt_feed(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Парсинг RSS-фида Freelancehunt"""
    url = "https://freelancehunt.com/projects.rss"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"
    }
    posts = []
    try:
        async with session.get(url, headers=headers, timeout=8) as resp:
            if resp.status != 200:
                return posts
            xml_text = await resp.text()
            root = ET.fromstring(xml_text)
            for it in root.findall(".//item"):
                t = it.find("title").text if it.find("title") is not None else ""
                d = it.find("description").text if it.find("description") is not None else ""
                link = it.find("link").text if it.find("link") is not None else ""
                
                clean_desc = re.sub(r"<[^>]+>", " ", d).strip()
                full_text = f"{t}\n\n{clean_desc}"
                
                lead = analyze_lead(full_text)
                if lead:
                    lead["channel"] = "Freelancehunt"
                    lead["link"] = link
                    posts.append(lead)
    except Exception:
        pass
    return posts

async def fetch_kwork_feed(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Парсинг биржи Kwork через stateData JSON"""
    posts = []
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    # 81 = Разработка игр, 61 = Обучение и консалтинг, 11 = Скрипты и боты
    target_cats = [81, 61, 11]
    
    for cat_id in target_cats:
        url = f"https://kwork.ru/projects?c={cat_id}"
        try:
            async with session.get(url, headers=headers, timeout=8) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()
                idx = html.find("window.stateData")
                if idx == -1:
                    continue
                sub = html[idx + len("window.stateData"):]
                sub = sub[sub.find("{"):]
                
                try:
                    obj, _ = json.JSONDecoder().raw_decode(sub)
                    wants = obj.get("wants", [])
                    for w in wants:
                        name = w.get("name", "")
                        desc = w.get("description", "")
                        order_id = w.get("id")
                        price = w.get("priceLimit") or w.get("possiblePriceLimit")
                        
                        clean_desc = re.sub(r"<[^>]+>", " ", desc).strip()
                        full_text = f"{name}\n\n{clean_desc}"
                        
                        lead = analyze_lead(full_text)
                        if lead:
                            price_str = f"{price} ₽" if price else "По договоренности"
                            lead["channel"] = "Kwork (IT/GameDev)"
                            lead["link"] = f"https://kwork.ru/projects/{order_id}"
                            lead["price"] = price_str
                            posts.append(lead)
                except Exception:
                    pass
        except Exception:
            pass
    return posts

async def scan_all() -> List[Dict[str, Any]]:
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        # Параллельный сбор со всех каналов и бирж (без мертвого Kwork)
        tasks = [fetch_channel_posts(session, ch) for ch in CHANNELS]
        tasks.append(fetch_fl_feed(session))
        tasks.append(fetch_freelancehunt_feed(session))
        
        results = await asyncio.gather(*tasks)
        
        flat_results = []
        for res in results:
            flat_results.extend(res)
        return flat_results
