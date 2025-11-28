# -*- coding: utf-8 -*-
"""
ASCII-safe copy of your bot that forces UTF-8 output when possible and avoids emojis
to prevent "Some characters could not be decoded" problems in terminals that are not UTF-8.
This file intentionally keeps the literal token/chat id (as requested).
"""

import json
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import logging
import sys

# Try to force stdout/stderr to UTF-8 when supported (Python 3.7+)
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Disable warnings from urllib3 about certificates if you keep verify=False
requests.packages.urllib3.disable_warnings()

# === USING LITERAL TOKEN & CHAT ID (as requested) ===
TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"
# ===================================================

SCRAPE_LINKS = {
    'Casa.it': 'https://www.casa.it/srp/?tr=vendita&numRoomsMin=3&mqMin=80&priceMax=360000&sortType=relevance&propertyTypeGroup=case&q=9f6485c2',
    'Idealista': 'https://www.idealista.it/vendita-case/milano-milano/con-prezzo_360000?dimensione_80=on&appartamenti=on&trilocali-3=on&quadrilocali-4=on&5-locali-o-piu=on&pubblicato_ultima-settimana=on&nuova-costruzione=on&buono-stato=on&senza-inquilini=on',
    'Subito': 'https://www.subito.it/annunci-lombardia/vendita/appartamenti/milano/',
    'Tecnocasa': 'https://www.tecnocasa.it/annunci/immobili/lombardia/milano/milano.html?min_rooms=3&heating=1,3',
    'Grimaldi': 'https://www.grimaldifranchising.it/vendita/appartamenti/mi/milano?prezzo=360000&mq=80&numeroLocali=&numeroBagni=',
    'CaseTra': 'https://www.casetraprivati.it/vendita-case/milano'
}

class AntiBlockBot:
    """Bot with anti-block tactics (ASCII-safe prints)."""
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        self.referers = [
            'https://www.google.com/',
            'https://www.google.it/',
            'https://www.bing.com/',
            'https://duckduckgo.com/',
        ]
        # configure logging to not fail on non-utf output
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
        self.logger = logging.getLogger("AntiBlockBot")

    def get_rotating_headers(self):
        ua = random.choice(self.user_agents)
        ref = random.choice(self.referers)
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': ref,
        }

    def create_session(self):
        session = requests.Session()
        retry_strategy = Retry(
            total=6,
            backoff_factor=random.uniform(0.5, 1.0),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            respect_retry_after_header=True
        )
        adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=10)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.verify = False  # keep same behavior as original; change if desired
        return session

    def get_with_rotation(self, url, max_retries=5):
        for attempt in range(max_retries):
            try:
                session = self.create_session()
                headers = self.get_rotating_headers()
                if attempt > 0:
                    delay = random.uniform(2 ** (attempt - 1), 2 ** attempt)
                    time.sleep(min(delay, 10))
                response = session.get(url, headers=headers, timeout=(10, 30), allow_redirects=True, verify=False)
                if response.status_code == 200:
                    return response
                else:
                    print(f"   WARN HTTP {response.status_code} for {url} (attempt {attempt+1}/{max_retries})")
                    # print small snippet when debugging
                    if attempt == max_retries - 1:
                        try:
                            print("   Response snippet:", response.text[:300].replace("\n", " "))
                        except Exception:
                            pass
                    time.sleep(1 + random.random())
            except requests.RequestException as e:
                print(f"   WARN RequestException: {e} (attempt {attempt+1}/{max_retries})")
                time.sleep(1 + random.random())
        return None

    def extract_listings(self, soup, site_name, max_items=5):
        listings = []
        try:
            selectors = [
                ('div', {'class': 'PropertyCard'}),
                ('article', {'class': 'item'}),
                ('article', {'class': 'property-card'}),
                ('li', {'class': 'result-item'}),
                ('div', {'class': 'listing-item'}),
                ('a', {'class': 'item-link'}),
            ]
            items = []
            for tag, attrs in selectors:
                items = soup.find_all(tag, attrs)
                if items:
                    break
            print(f"   {site_name}: {len(items)} elements found")
            for item in items[:max_items]:
                try:
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue
                    link = link_elem.get('href', '').strip()
                    title = (link_elem.get('title') or link_elem.text or "").strip()
                    if not link or not title:
                        continue
                    if link.startswith('/'):
                        base_url = self.get_base_url(site_name)
                        link = base_url + link
                    elif not link.startswith('http'):
                        base_url = self.get_base_url(site_name)
                        link = base_url + '/' + link
                    # price
                    price = 0
                    for tag, attrs in [('span', {'class': 'item-price'}), ('span', {'class': 'price'}), ('div', {'class': 'price'})]:
                        price_elem = item.find(tag, attrs)
                        if price_elem:
                            price_text = price_elem.get_text(strip=True)
                            digits = ''.join(filter(str.isdigit, price_text))
                            if digits:
                                price = int(digits)
                            break
                    text = item.get_text(" ", strip=True).lower()
                    mq = 0
                    for word in text.split():
                        if 'mq' in word:
                            num = ''.join(filter(str.isdigit, word))
                            if num:
                                mq = int(num)
                                break
                    rooms = 0
                    if any(x in text for x in ['trilocale', 'tre locali', '3 locali']):
                        rooms = 3
                    elif any(x in text for x in ['quadrilocale', 'quattro locali', '4 locali']):
                        rooms = 4
                    elif any(x in text for x in ['bilocale', '2 locali']):
                        rooms = 2
                    zone = 'Milano'
                    for tag, attrs in [('span', {'class': 'item-location'}), ('span', {'class': 'location'}), ('div', {'class': 'zone'})]:
                        zone_elem = item.find(tag, attrs)
                        if zone_elem:
                            zone = zone_elem.get_text(strip=True)
                            break
                    if price and price <= 360000 and mq >= 80 and rooms >= 3:
                        listings.append({
                            'title': title[:100],
                            'price': price,
                            'mq': mq,
                            'rooms': rooms,
                            'zone': zone,
                            'description': title[:100],
                            'link': link,
                            'images': [],
                            'source': site_name
                        })
                except Exception:
                    continue
        except Exception as e:
            print(f"   ERROR parsing {site_name}: {e}")
        return listings

    def get_base_url(self, site_name):
        bases = {
            'Casa.it': 'https://www.casa.it',
            'Idealista': 'https://www.idealista.it',
            'Subito': 'https://www.subito.it',
            'Tecnocasa': 'https://www.tecnocasa.it',
            'Grimaldi': 'https://www.grimaldifranchising.it',
            'CaseTra': 'https://www.casetraprivati.it'
        }
        return bases.get(site_name, 'https://www.google.com')

    def scrape_site(self, site_name, url):
        print(f"   Downloading {site_name} ...")
        response = self.get_with_rotation(url)
        if not response:
            print(f"   Could not download {site_name}")
            return []
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = self.extract_listings(soup, site_name)
            return listings
        except Exception as e:
            print(f"   ERROR parsing {site_name}: {e}")
            return []

    def invia_telegram(self, listing):
        text_message = (
            f"Title: {listing['title']}\n\n"
            f"Price: €{listing['price']:,}\n"
            f"Size: {listing['mq']} mq\n"
            f"Rooms: {listing['rooms']}\n"
            f"Zone: {listing['zone']}\n\n"
            f"Link: {listing['link']}\n"
            f"Time: {listing.get('timestamp','')}"
        )
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            payload = {
                'chat_id': CHAT_ID,
                'text': text_message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': False
            }
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                print(f"   Telegram: sent {listing['title'][:50]}")
                return True
            else:
                print(f"   Telegram failed {response.status_code}: {response.text[:200]}")
        except Exception as e:
            print(f"   Telegram error: {e}")
        return False

    def load_seen_listings(self):
        try:
            if os.path.exists('listing_visti.json'):
                with open('listing_visti.json', 'r', encoding='utf-8') as f:
                    return set(json.load(f))
        except Exception:
            pass
        return set()

    def save_seen_listings(self, seen):
        try:
            with open('listing_visti.json', 'w', encoding='utf-8') as f:
                json.dump(list(seen), f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def run(self):
        print("=" * 60)
        print("HOUSE FINDER MILANO - START")
        print("=" * 60)
        print(f"Time: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print("Scraping 6 sites with filters: price <= 360000, size >= 80, rooms >= 3")
        print("=" * 60)

        seen = self.load_seen_listings()
        print(f"Already sent: {len(seen)}")

        all_listings = []
        for site_name, url in SCRAPE_LINKS.items():
            try:
                listings = self.scrape_site(site_name, url)
                all_listings.extend(listings)
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"   Error for {site_name}: {e}")
                continue

        if not all_listings:
            print("No listings found.")
            return

        all_listings.sort(key=lambda x: x['price'])
        top3 = all_listings[:3]

        new_count = 0
        for listing in top3:
            listing['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
            listing_id = f"{listing['price']}_{listing['mq']}_{listing['link']}"
            if listing_id not in seen:
                print("New listing found:")
                print(f"  {listing['title'][:70]}")
                print(f"  {listing['mq']} mq | €{listing['price']:,}")
                self.invia_telegram(listing)
                seen.add(listing_id)
                new_count += 1
                time.sleep(random.uniform(1, 3))

        if new_count > 0:
            print(f"{new_count} listings sent to Telegram.")
            self.save_seen_listings(seen)
        else:
            print("No new listings to send.")
        print("Run complete.")

if __name__ == "__main__":
    bot = AntiBlockBot()
    bot.run()
