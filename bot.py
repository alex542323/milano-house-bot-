import json
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random
import hashlib
from requests.cookies import RequestsCookieJar
import logging

# Disable warnings
requests.packages.urllib3.disable_warnings()

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

# LINK DA SCRAPARE
SCRAPE_LINKS = {
    'Casa.it': 'https://www.casa.it/srp/?tr=vendita&numRoomsMin=3&mqMin=80&priceMax=360000&sortType=relevance&propertyTypeGroup=case&q=9f6485c2',
    'Idealista': 'https://www.idealista.it/vendita-case/milano-milano/con-prezzo_360000?dimensione_80=on&appartamenti=on&trilocali-3=on&quadrilocali-4=on&5-locali-o-piu=on&pubblicato_ultima-settimana=on&nuova-costruzione=on&buono-stato=on&senza-inquilini=on',
    'Subito': 'https://www.subito.it/annunci-lombardia/vendita/appartamenti/milano/',
    'Tecnocasa': 'https://www.tecnocasa.it/annunci/immobili/lombardia/milano/milano.html?min_rooms=3&heating=1,3',
    'Grimaldi': 'https://www.grimaldifranchising.it/vendita/appartamenti/mi/milano?prezzo=360000&mq=80&numeroLocali=&numeroBagni=',
    'CaseTra': 'https://www.casetraprivati.it/vendita-case/milano'
}

class AntiBlockBot:
    """Bot con tecniche avanzate di bypass anti-detection"""
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
        ]
        
        self.referers = [
            'https://www.google.com/',
            'https://www.google.it/',
            'https://www.bing.com/',
            'https://www.yahoo.com/',
            'https://duckduckgo.com/',
            'https://www.baidu.com/',
            'https://www.ecosia.org/',
        ]
    
    def get_rotating_headers(self):
        """Headers randomizzati e realistici"""
        ua = random.choice(self.user_agents)
        ref = random.choice(self.referers)
        
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Referer': ref,
            'DNT': '1',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
        }
    
    def create_session(self):
        """Sessione con retry intelligenti e pool connections"""
        session = requests.Session()
        
        # Retry strategy aggressivo
        retry_strategy = Retry(
            total=8,
            backoff_factor=random.uniform(0.5, 1.5),
            status_forcelist=[403, 401, 429, 500, 502, 503, 504, 408, 409, 410, 425, 999],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            respect_retry_after_header=True
        )
        
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=10,
            pool_maxsize=10
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.verify = False
        
        return session
    
    def get_with_rotation(self, url, max_retries=5):
        """Scarica URL con rotazione completa di identificativi"""
        for attempt in range(max_retries):
            try:
                session = self.create_session()
                headers = self.get_rotating_headers()
                
                # Delay random tra i tentativi
                if attempt > 0:
                    delay = random.uniform(2 ** (attempt - 1), 2 ** attempt)
                    time.sleep(min(delay, 10))
                
                # Proxies random (opzionale)
                proxies = None
                
                response = session.get(
                    url,
                    headers=headers,
                    timeout=(10, 30),
                    proxies=proxies,
                    allow_redirects=True,
                    verify=False
                )
                
                # Gestione 403/401
                if response.status_code == 403:
                    print(f"   ⚠️ 403 - Tentativo {attempt+1}/{max_retries}, retry con headers diversi...")
                    time.sleep(random.uniform(1, 3))
                    continue
                
                elif response.status_code == 429:
                    print(f"   ⚠️ 429 Rate Limited - Aspetto e riprovo...")
                    retry_after = response.headers.get('Retry-After', str(2 ** attempt))
                    time.sleep(float(retry_after))
                    continue
                
                elif response.status_code in [500, 502, 503, 504, 408, 409]:
                    print(f"   ⚠️ {response.status_code} Server Error - Riprovo...")
                    time.sleep(random.uniform(2, 5))
                    continue
                
                elif response.status_code == 200:
                    return response
                
                else:
                    print(f"   ⚠️ Status {response.status_code} - Riprovo...")
                    time.sleep(random.uniform(1, 2))
                    continue
                    
            except requests.exceptions.ConnectTimeout:
                print(f"   ⚠️ Timeout connessione - Tentativo {attempt+1}/{max_retries}")
                time.sleep(random.uniform(2, 5))
                continue
            
            except requests.exceptions.ReadTimeout:
                print(f"   ⚠️ Timeout lettura - Tentativo {attempt+1}/{max_retries}")
                time.sleep(random.uniform(2, 5))
                continue
            
            except requests.exceptions.ConnectionError:
                print(f"   ⚠️ Errore connessione - Tentativo {attempt+1}/{max_retries}")
                time.sleep(random.uniform(3, 7))
                continue
            
            except Exception as e:
                print(f"   ⚠️ Errore: {str(e)[:50]} - Tentativo {attempt+1}/{max_retries}")
                time.sleep(random.uniform(2, 4))
                continue
        
        return None
    
    def extract_listings(self, soup, site_name, max_items=5):
        """Estrae listing con parsing robusto"""
        listings = []
        
        try:
            items = []
            
            # Selettori multipli per robustezza
            selectors = [
                ('div', {'class': 'PropertyCard'}),
                ('article', {'class': 'item'}),
                ('article', {'class': 'property-card'}),
                ('li', {'class': 'result-item'}),
                ('div', {'class': 'listing-item'}),
                ('a', {'class': 'item-link'}),
            ]
            
            for tag, attrs in selectors:
                items = soup.find_all(tag, attrs)
                if items:
                    break
            
            print(f"   ✅ {site_name}: {len(items)} elementi trovati")
            
            for item in items[:max_items]:
                try:
                    # Estrai link
                    link_elem = item.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    link = link_elem.get('href', '').strip()
                    title = link_elem.get('title', '').strip() or link_elem.text.strip()
                    
                    if not link or not title:
                        continue
                    
                    # Completa URL relativo
                    if link.startswith('/'):
                        base_url = self.get_base_url(site_name)
                        link = base_url + link
                    elif not link.startswith('http'):
                        base_url = self.get_base_url(site_name)
                        link = base_url + '/' + link
                    
                    # Estrai prezzo
                    price = 0
                    price_patterns = [
                        ('span', {'class': 'item-price'}),
                        ('span', {'class': 'price'}),
                        ('div', {'class': 'price'}),
                    ]
                    
                    for tag, attrs in price_patterns:
                        price_elem = item.find(tag, attrs)
                        if price_elem:
                            price_text = price_elem.text.strip()
                            price_digits = ''.join(filter(str.isdigit, price_text))
                            if price_digits:
                                price = int(price_digits)
                            break
                    
                    # Estrai metratura e camere
                    text = item.get_text().lower()
                    
                    mq = 0
                    for word in text.split():
                        if 'mq' in word:
                            num = ''.join(filter(str.isdigit, word))
                            if num:
                                mq = int(num)
                                break
                    
                    rooms = 0
                    if any(x in text for x in ['trilocale', 'tre locali', '3 locali', '3hab']):
                        rooms = 3
                    elif any(x in text for x in ['quadrilocale', 'quattro locali', '4 locali', '4hab']):
                        rooms = 4
                    elif any(x in text for x in ['bilocale', '2 locali', '2hab']):
                        rooms = 2
                    
                    # Estrai zona
                    zone = 'Milano'
                    zone_patterns = [
                        ('span', {'class': 'item-location'}),
                        ('span', {'class': 'location'}),
                        ('div', {'class': 'zone'}),
                    ]
                    
                    for tag, attrs in zone_patterns:
                        zone_elem = item.find(tag, attrs)
                        if zone_elem:
                            zone = zone_elem.text.strip()
                            break
                    
                    # Filtro finale
                    if price <= 360000 and mq >= 80 and rooms >= 3:
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
                
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"   ❌ Errore parsing {site_name}: {e}")
        
        return listings
    
    def get_base_url(self, site_name):
        """Base URL per i siti"""
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
        """Scrapa un sito completo"""
        print(f"   📍 Scaricando {site_name}...")
        
        response = self.get_with_rotation(url)
        if not response:
            print(f"   ❌ Impossibile scaricare {site_name}")
            return []
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            listings = self.extract_listings(soup, site_name)
            return listings
        
        except Exception as e:
            print(f"   ❌ Errore parsing {site_name}: {e}")
            return []
    
    def invia_telegram(self, listing):
        """Invia su Telegram"""
        text_message = f"""🏠 <b>{listing['title']}</b>

💰 €{listing['price']:,}
📐 {listing['mq']} mq
🛏️ {listing['rooms']} camere
📍 {listing['zone']}

📝 {listing['description']}

🔗 <a href="{listing['link']}">Visualizza su {listing['source']}</a>

⏰ {listing['timestamp']}"""
        
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
            params = {
                'chat_id': CHAT_ID,
                'text': text_message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': 'false'
            }
            response = requests.post(url, params=params, timeout=10)
            
            if response.status_code == 200:
                print(f"   ✅ Telegram: {listing['title'][:40]}")
                return True
        
        except Exception as e:
            print(f"   ❌ Telegram: {str(e)[:50]}")
        
        return False
    
    def load_seen_listings(self):
        """Carica listing già inviati"""
        try:
            if os.path.exists('listing_visti.json'):
                with open('listing_visti.json', 'r') as f:
                    return set(json.load(f))
        except:
            pass
        return set()
    
    def save_seen_listings(self, seen):
        """Salva listing inviati"""
        try:
            with open('listing_visti.json', 'w') as f:
                json.dump(list(seen), f)
        except:
            pass
    
    def run(self):
        """Main loop"""
        print("=" * 70)
        print("🚀 BOT HOUSE FINDER MILANO - VERSIONE PROFESSINALE ANTI-BLOCK")
        print("=" * 70)
        print(f"⏰ Ora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        print(f"📊 Scrapa da: 6 SITI LIVE")
        print(f"   Filtri: Prezzo max €360k, Mq min 80, Min 3 locali")
        print(f"   Sistema: Anti-403/429 + Headers Rotating + Retry 8x")
        print("=" * 70)
        
        seen = self.load_seen_listings()
        print(f"📚 Listing già inviati: {len(seen)}\n")
        
        all_listings = []
        
        # Scrapa tutti i siti
        for site_name, url in SCRAPE_LINKS.items():
            try:
                listings = self.scrape_site(site_name, url)
                all_listings.extend(listings)
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"   ❌ Errore {site_name}: {e}")
                continue
        
        if not all_listings:
            print("❌ Nessun listing trovato")
            return
        
        # Top 3 per prezzo
        all_listings.sort(key=lambda x: x['price'])
        listings = all_listings[:3]
        
        print(f"\n   📄 Top 3 Listing selezionati da {len(all_listings)} totali\n")
        
        nuovi = 0
        for listing in listings:
            listing['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
            listing_id = f"{listing['price']}_{listing['mq']}_{listing['link']}"
            
            if listing_id not in seen:
                print(f"   🆕 NUOVO ({listing['source']}):")
                print(f"      {listing['title'][:60]}")
                print(f"      {listing['mq']} mq | €{listing['price']:,}")
                
                self.invia_telegram(listing)
                seen.add(listing_id)
                nuovi += 1
                time.sleep(random.uniform(1, 3))
        
        print()
        if nuovi > 0:
            print(f"✅ {nuovi} LISTING INVIATO/I SU TELEGRAM")
            self.save_seen_listings(seen)
        else:
            print(f"✅ Nessun nuovo listing")
        
        print(f"\n✅ Prossima esecuzione tra 5 minuti!")

if __name__ == "__main__":
    bot = AntiBlockBot()
    bot.run()
