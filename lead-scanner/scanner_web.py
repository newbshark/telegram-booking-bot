import re
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from analyzer import PUBLIC_CHANNELS, analyze_job

async def fetch_channel_posts(session: aiohttp.ClientSession, channel: str) -> List[Dict[str, str]]:
    url = f"https://t.me/s/{channel}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    posts = []
    try:
        async with session.get(url, headers=headers, timeout=10) as resp:
            if resp.status != 200:
                return posts
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            
            # Сообщения в t.me/s
            message_nodes = soup.find_all("div", class_="tgme_widget_message")
            for node in message_nodes:
                text_node = node.find("div", class_="tgme_widget_message_text")
                link_node = node.find("a", class_="tgme_widget_message_date")
                if not text_node or not link_node:
                    continue
                
                text = text_node.get_text(separator="\n").strip()
                link = link_node.get("href", "")
                
                posts.append({
                    "channel": channel,
                    "text": text,
                    "link": link
                })
    except Exception as e:
        pass
    return posts

async def fetch_kwork_feed(session: aiohttp.ClientSession) -> List[Dict[str, str]]:
    posts = []
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
    }
    for page in [1, 2]:
        url = f"https://kwork.ru/projects?page={page}"
        try:
            async with session.get(url, headers=headers, timeout=8) as resp:
                if resp.status != 200:
                    continue
                html = await resp.text()
                for block in re.split(r'\{\"userAlreadyWork\"', html)[1:]:
                    m_id = re.search(r'\"id\":(\d+)', block)
                    m_title = re.search(r'\"title\":\"(.*?)\"', block)
                    m_desc = re.search(r'\"description\":\"(.*?)\",\"(?:files|category_id|user_id)', block)
                    m_price = re.search(r'\"possiblePriceLimit\":(\d+)', block)
                    m_offers = re.search(r'\"kwork_count\":(\d+)', block)
                    
                    if m_id and m_desc:
                        pid = m_id.group(1)
                        title = m_title.group(1) if m_title else ""
                        desc = m_desc.group(1).replace(r'\"', '"').replace("\r\n", " ").replace("\n", " ")
                        price = m_price.group(1) if m_price else "договорная"
                        offers = int(m_offers.group(1)) if m_offers else 0
                        
                        # Only take projects with reasonable competition
                        if offers <= 25:
                            full_text = f"{title}. {desc} (Бюджет: {price} ₽, откликов: {offers})"
                            posts.append({
                                "channel": f"kwork_proj_{pid}",
                                "text": full_text,
                                "link": f"https://kwork.ru/projects/{pid}/view"
                            })
        except Exception:
            pass
    return posts

async def scan_all_channels() -> List[Dict[str, Any]]:
    results = []
    connector = aiohttp.TCPConnector(ssl=False)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch_channel_posts(session, ch) for ch in PUBLIC_CHANNELS]
        tasks.append(fetch_kwork_feed(session))
        all_posts_lists = await asyncio.gather(*tasks)
        
        for posts in all_posts_lists:
            for p in posts:
                analysis = analyze_job(p["text"])
                if analysis["status"] == "ACCEPT":
                    results.append({
                        "channel": p["channel"],
                        "link": p["link"],
                        "text": p["text"],
                        "category": analysis["category"],
                        "score": analysis["score"],
                        "proposal": analysis["proposal"],
                        "contact": analysis.get("contact", "")
                    })
    return results
