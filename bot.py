import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import re

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

def scrape_immobiliare():
    url = "https://www.immobiliare.it/vendita-case/milano/con-riscaldamento-autonomo/?prezzoMassimo=400000&superficieMinima=80&localiMinimo=3&tipoProprieta=1"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"❌ Errore nel download: {e}")
        return None

def parse_listings(html):
    if not html:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    listings = []
    try:
        items = soup.find_all('article', {'data-testid': 'property-card'})
        if not items:
            items = soup.find_all('div', class_=re.compile('.*property.*card.*', re.I))
        print(f"   📄 Card trovate: {len(items)}")
        for item in items:
            try:
                link_elem = item.find('a', {'data-testid': re.compile('.*link.*', re.I)})
                if not link_elem:
                    link_elem = item.find('a', href=True)
                link = link_elem.get('href') if link_elem else None
                if not link:
                    continue
                if not link.startswith('http'):
                    link = "https://www.immobiliare.it" + link
                listing_id = link.split('/')[-2] if '/' in link else str(datetime.now().timestamp())
                title_elem = item.find('h2') or item.find('h3')
                title = title_elem.text.strip() if title_elem else "N/A"
                price_elem = item.find('span', {'data-testid': re.compile('.*price.*', re.I)})
                if not price_elem:
                    price_elem = item.find(string=re.compile(r'€.*\d+'))
                price_text = price_elem.text.strip() if price_elem else "0"
                try:
                    price = int(re.sub(r'[^\d]', '', price_text))
                except:
                    price = 0
                mq = 0
                mq_text = item.get_text()
                mq_match = re.search(r'(\d+)\s*(?:mq|m²|m2)', mq_text, re.I)
                if mq_match:
                    try:
                        mq = int(mq_match.group(1))
                    except:
                        pass
                rooms = 0
                rooms_match = re.search(r'(\d+)\s*(?:camera|camere|stanze)', mq_text, re.I)
                if rooms_match:
                    try:
                        rooms = int(rooms_match.group(1))
                    except:
                        pass
                desc_elem = item.find('p')
                description = desc_elem.text.strip() if desc_elem else title
                full_text = (title + " " + description).lower()
                if 'nuda propriet' in full_text or 'nuda proprietà' in full_text:
                    continue
                listing = {
                    'id': listing_id,
                    'title': title,
                    'price': price,
                    'mq': mq,
                    'rooms': rooms,
                    'description': description[:200],
                    'link': link,
                    'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
                }
                listings.append(listing)
            except Exception as e:
                print(f"   ⚠️ Errore nel parsing: {str(e)[:50]}")
                continue
        return listings
    except Exception as e:
        print(f"❌ Errore generale nel parsing: {e}")
        return []

def invia_telegram(listing):
    message = f"""
🏠 <b>NUOVO LISTING TROVATO!</b>

<b>{listing['title']}</b>

💰 Prezzo: €{listing['price']:,}
📐 Mq: {listing['mq']}
🛏️ Camere: {listing['rooms'] if listing['rooms'] > 0 else 'N/A'}

📝 <i>{listing['description']}</i>

🔗 <a href="{listing['link']}">Visualizza Annuncio Completo</a>

⏰ {listing['timestamp']}
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    params = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'HTML',
        'disable_web_page_preview': 'true'
    }
    try:
        response = requests.post(url, params=params, timeout=10)
        if response.status_code == 200:
            print(f"   ✅ Messaggio inviato: {listing['title'][:50]}")
            return True
        else:
            print(f"   ❌ Errore Telegram: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Errore nell'invio: {e}")
        return False

def carica_listing_visti():
    try:
        if os.path.exists('listing_visti.json'):
            with open('listing_visti.json', 'r') as f:
                return set(json.load(f))
    except:
        pass
    return set()

def salva_listing_visti(visti):
    try:
        with open('listing_visti.json', 'w') as f:
            json.dump(list(visti), f)
    except:
        pass

def main():
    print("=" * 70)
    print("🚀 BOT HOUSE FINDER MILANO AVVIATO!")
    print("=" * 70)
    print(f"⏰ Ora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"🔗 URL: https://www.immobiliare.it/vendita-case/milano/")
    print(f"   Filtri: Prezzo max €400k, Mq min 60, Min 3 locali")
    print(f"🚫 Escluse: Nuda proprietà")
    print("=" * 70)
    
    listing_visti = carica_listing_visti()
    print(f"📚 Listing già monitorati: {len(listing_visti)}\n")
    
    print("🌐 Download pagina Immobiliare.it...")
    html = scrape_immobiliare()
    if not html:
        print("❌ Errore nel download")
        return
    
    print("✅ Pagina scaricata")
    
    print("📊 Parsing dei listing...")
    listings = parse_listings(html)
    print(f"   📄 Total listing trovati: {len(listings)}")
    
    nuovi = 0
    for listing in listings:
        if listing['id'] not in listing_visti:
            print(f"\n   🆕 NUOVO LISTING:")
            print(f"      Titolo: {listing['title'][:60]}")
            print(f"      Prezzo: €{listing['price']:,}")
            print(f"      Mq: {listing['mq']} | Camere: {listing['rooms'] if listing['rooms'] > 0 else 'N/A'}")
            
            invia_telegram(listing)
            listing_visti.add(listing['id'])
            nuovi += 1
    
    if nuovi > 0:
        print(f"\n📬 TOTALE MESSAGGI INVIATI: {nuovi}")
        salva_listing_visti(listing_visti)
    else:
        print(f"\n😴 Nessun nuovo listing trovato")
    
    print(f"\n✅ Esecuzione completata! Il bot girerà di nuovo tra 5 minuti.")

if __name__ == "__main__":
    main()
