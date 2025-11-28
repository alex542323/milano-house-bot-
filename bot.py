import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import re
import time

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

def scrape_immobiliare():
    url = "https://www.immobiliare.it/vendita-case/milano/?prezzoMassimo=400000&superficieMinima=80&localiMinimo=3"
    
    try:
        scraper = cloudscraper.create_scraper()
        response = scraper.get(url, timeout=30)
        response.raise_for_status()
        print(f"✅ Download riuscito (Status: {response.status_code})")
        return response.text
    except Exception as e:
        print(f"❌ Errore nel download: {e}")
        return None

def extract_images(item):
    images = []
    try:
        img_elements = item.find_all('img')
        for img in img_elements[:10]:
            img_url = img.get('src') or img.get('data-src')
            if img_url and ('pwm.im-cdn.it' in img_url or 'immobiliare' in img_url.lower()):
                if img_url not in images and len(images) < 10:
                    images.append(img_url)
        return images
    except:
        return []

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
        
        for item in items[:30]:
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
                
                images = extract_images(item)
                
                listing = {
                    'id': listing_id,
                    'title': title,
                    'price': price,
                    'mq': mq,
                    'rooms': rooms,
                    'description': description[:200],
                    'link': link,
                    'images': images,
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
    text_message = f"""🏠 <b>NUOVO LISTING TROVATO!</b>

<b>{listing['title']}</b>

💰 Prezzo: €{listing['price']:,}
📐 Mq: {listing['mq']}
🛏️ Camere: {listing['rooms'] if listing['rooms'] > 0 else 'N/A'}

📝 <i>{listing['description']}</i>

🔗 <a href="{listing['link']}">Visualizza Annuncio Completo</a>

⏰ {listing['timestamp']}"""
    
    try:
        import requests
        if listing['images'] and len(listing['images']) > 0:
            media_group = []
            for idx, img_url in enumerate(listing['images'][:10]):
                try:
                    media_group.append({
                        "type": "photo",
                        "media": img_url,
                        "caption": text_message if idx == 0 else "",
                        "parse_mode": "HTML"
                    })
                except:
                    continue
            
            if media_group:
                url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMediaGroup"
                params = {
                    'chat_id': CHAT_ID,
                    'media': json.dumps(media_group)
                }
                response = requests.post(url, params=params, timeout=20)
                if response.status_code == 200:
                    print(f"   ✅ Album inviato ({len(media_group)} foto): {listing['title'][:40]}")
                    return True
                else:
                    print(f"   ⚠️ Errore Album ({response.status_code}), provo con messaggio testo")
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': CHAT_ID,
            'text': text_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'true'
        }
        import requests
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
    print(f"   Filtri: Prezzo max €400k, Mq min 80, Min 3 locali")
    print(f"📸 Foto: SI - Tutte le immagini disponibili")
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
            print(f"      Foto: {len(listing['images'])}")
            
            invia_telegram(listing)
            listing_visti.add(listing['id'])
            nuovi += 1
            time.sleep(1)
    
    if nuovi > 0:
        print(f"\n📬 TOTALE MESSAGGI INVIATI: {nuovi}")
        salva_listing_visti(listing_visti)
    else:
        print(f"\n😴 Nessun nuovo listing trovato")
    
    print(f"\n✅ Esecuzione completata! Il bot girerà di nuovo tra 5 minuti.")

if __name__ == "__main__":
    main()
