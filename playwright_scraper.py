#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright-based scraper that loads JS pages, extracts listings and sends them to Telegram.
This file intentionally uses the literal TELEGRAM_TOKEN and CHAT_ID (as requested).
"""
import time
import random
import json
import re
from datetime import datetime
from urllib.parse import urlparse, urljoin
import os
import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# === LITERAL TOKEN & CHAT ID (as requested) ===
TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"
# ==============================================

# Sites to scrape
SCRAPE_LINKS = {
    'Casa.it': 'https://www.casa.it/srp/?tr=vendita&numRoomsMin=3&mqMin=80&priceMax=360000&sortType=relevance&propertyTypeGroup=case&q=9f6485c2',
    'Idealista': 'https://www.idealista.it/vendita-case/milano-milano/con-prezzo_360000?dimensione_80=on&appartamenti=on&trilocali-3=on&quadrilocali-4=on&5-locali-o-piu=on&pubblicato_ultima-settimana=on&nuova-costruzione=on&buono-stato=on&senza-inquilini=on',
    'Subito': 'https://www.subito.it/annunci-lombardia/vendita/appartamenti/milano/',
    'Tecnocasa': 'https://www.tecnocasa.it/annunci/immobili/lombardia/milano/milano.html?min_rooms=3&heating=1,3',
    'Grimaldi': 'https://www.grimaldifranchising.it/vendita-appartamenti/mi/milano?prezzo=360000&mq=80&numeroLocali=&numeroBagni=',
    'CaseTra': 'https://www.casetraprivati.it/vendita-case/milano'
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

LISTING_STORE = "listing_visti.json"

def normalize_link(link, base):
    link = (link or "").strip()
    if not link:
        return ""
    if link.startswith("//"):
        parsed = urlparse(base)
        return f"{parsed.scheme}:{link}"
    if link.startswith("/"):
        return urljoin(base, link)
    if not link.startswith("http"):
        return urljoin(base + "/", link)
    return link

def extract_listings_from_html(html, site_name, base_url, max_items=6):
    soup = BeautifulSoup(html, "html.parser")
    results = []

    selectors = [
        "article.property-card", "div.PropertyCard", "div.card-listing",
        "li.annuncio", "div.listing-item", "article.item", "div.adItem",
        "div.result-item", "div.offer"
    ]
    items = []
    for sel in selectors:
        items = soup.select(sel)
        if items:
            break

    # fallback: any anchor-like elements if no structured items
    if not items:
        items = soup.find_all("a", href=True)

    for item in items[:max_items]:
        try:
            a = item.find("a", href=True) or (item if item.name == "a" else None)
            if a:
                href = a.get("href")
            else:
                href = item.get("href") if hasattr(item, "get") else ""
            link = normalize_link(href, base_url)
            title = (a.get("title") if a else "") or (a.get_text(" ", strip=True) if a else item.get_text(" ", strip=True))
            text = item.get_text(" ", strip=True).lower()
            # price
            price = 0
            price_elem = item.find(lambda tag: tag.name in ["span", "div"] and re.search(r"€|\beuro", tag.get_text("", strip=True).lower()))
            if price_elem:
                ptxt = price_elem.get_text("", strip=True)
            else:
                ptxt = text
            m = re.search(r"€\s?([\d\.\s,]+)", ptxt)
            if m:
                digits = re.sub(r"[^\d]", "", m.group(1))
                if digits:
                    price = int(digits)
            # mq
            mq = 0
            m2 = re.search(r"(\d{2,4})\s?m(?:q|²|2|q)", text)
            if m2:
                mq = int(m2.group(1))
            # rooms
            rooms = 0
            if re.search(r"\b(trilocale|3 locali|3 camere)\b", text):
                rooms = 3
            elif re.search(r"\b(quadrilocale|4 locali|4 camere)\b", text):
                rooms = 4
            elif re.search(r"\b(bilocale|2 locali|2 camere)\b", text):
                rooms = 2
            # zone
            zone = "Milano"
            zn = item.find(lambda t: t.name in ["span", "div"] and re.search(r"milano|milan", t.get_text("", strip=True), re.I))
            if zn:
                zone = zn.get_text(" ", strip=True)
            # filter
            if price and price <= 360000 and mq >= 80 and rooms >= 3:
                results.append({
                    "title": (title or link)[:200],
                    "price": price,
                    "mq": mq,
                    "rooms": rooms,
                    "zone": zone,
                    "description": (title or "")[:250],
                    "link": link,
                    "source": site_name
                })
        except Exception:
            continue

    # page-wide regex fallback
    if not results:
        snippets = re.findall(r"(.{0,120}€[\d\.\s,]{1,30}.{0,120}mq.{0,120})", html, flags=re.I | re.S)
        for s in snippets[:max_items]:
            m_price = re.search(r"€\s?([\d\.\s,]+)", s)
            m_mq = re.search(r"(\d{2,4})\s?m(?:q|²|2|q)", s)
            if m_price and m_mq:
                price = int(re.sub(r"[^\d]", "", m_price.group(1)))
                mq = int(m_mq.group(1))
                if price <= 360000 and mq >= 80:
                    results.append({
                        "title": s[:120],
                        "price": price,
                        "mq": mq,
                        "rooms": 3,
                        "zone": "Milano",
                        "description": s[:200],
                        "link": "",
                        "source": site_name
                    })

    return results

def send_telegram(listing):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    text_message = (
        f"{listing['title']}\n\n"
        f"€{listing['price']:,} | {listing['mq']} mq | {listing['rooms']} rooms\n"
        f"{listing['zone']}\n\n"
        f"{listing.get('link','')}\n\n"
        f"{listing.get('timestamp','')}"
    )
    payload = {"chat_id": CHAT_ID, "text": text_message, "disable_web_page_preview": False}
    try:
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            return True
        else:
            print("Telegram error:", r.status_code, r.text)
            return False
    except Exception as e:
        print("Telegram request exception:", e)
        return False

def scrape_with_playwright(url, headless=True, timeout=30000):
    ua = random.choice(USER_AGENTS)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=ua, locale="it-IT")
        page = context.new_page()
        try:
            page.set_viewport_size({"width": 1280, "height": 800})
            page.goto(url, wait_until="networkidle", timeout=timeout)
            time.sleep(random.uniform(2.0, 4.0))
            # try to accept cookie banner
            for sel in ["button:has-text('Accetta')", "button:has-text('OK')", "button:has-text('Accetto')", "button:has-text('Accept')"]:
                try:
                    els = page.query_selector_all(sel)
                    for el in els:
                        try:
                            el.click(timeout=1000)
                            time.sleep(0.2)
                        except Exception:
                            pass
                except Exception:
                    pass
            content = page.content()
        except Exception as e:
            print("Playwright error for", url, ":", e)
            try:
                content = page.content()
            except Exception:
                content = ""
        finally:
            try:
                context.close()
            except Exception:
                pass
            browser.close()
    return content

def main():
    print("="*60)
    print("Playwright scraper run -", datetime.now().isoformat())
    print("="*60)
    all_listings = []
    for site_name, url in SCRAPE_LINKS.items():
        print("Loading", site_name, "...")
        html = scrape_with_playwright(url, headless=True)
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        listings = extract_listings_from_html(html, site_name, base_url)
        print(f"  {site_name}: extracted {len(listings)} listings")
        all_listings.extend(listings)
        time.sleep(random.uniform(1.0, 3.0))

    if not all_listings:
        print("No listings found. Sending debug message to Telegram.")
        try:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                          json={"chat_id": CHAT_ID, "text": f"No listings found on {datetime.now().isoformat()} (Playwright run)", "disable_web_page_preview": True}, timeout=10)
        except Exception as e:
            print("Failed to send diagnostic telegram:", e)
        return

    all_listings.sort(key=lambda x: x.get("price", 10**12))
    top = all_listings[:3]
    sent = 0
    seen = set()
    if os.path.exists(LISTING_STORE):
        try:
            with open(LISTING_STORE, "r", encoding="utf-8") as f:
                seen = set(json.load(f))
        except Exception:
            seen = set()

    for l in top:
        l["timestamp"] = datetime.now().strftime("%d/%m/%Y %H:%M")
        lid = f"{l.get('price','0')}_{l.get('mq','0')}_{l.get('link','')}"
        if lid in seen:
            print("Already seen:", l.get("title")[:80])
            continue
        ok = send_telegram(l)
        if ok:
            sent += 1
            seen.add(lid)
        time.sleep(random.uniform(1.0, 3.0))

    if sent > 0:
        with open(LISTING_STORE, "w", encoding="utf-8") as f:
            json.dump(sorted(list(seen)), f, ensure_ascii=False, indent=2)
    print(f"Done. Sent {sent} new listings.")

if __name__ == "__main__":
    main()
