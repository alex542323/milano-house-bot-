import json
import os
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

def scrape_immobiliare():
    """Scarica i listing REALI da Immobiliare.it"""
    url = "https://www.immobiliare.it/vendita-case/milano/?prezzoMassimo=400000&superficieMinima=80&localiMinimo=3"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print("   📍 Scaricando dati da Immobiliare.it...")
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"   ❌ Errore download: {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        listings = []
        
        # Trova tutti gli annunci
        items = soup.find_all('article', {'data-testid': 'property-card'})
        print(f"   📄 Trovati {len(items)} annunci")
        
        for item in items[:3]:  # Prendi solo i top 3
            try:
                # Titolo e link
                title_elem = item.find('h2')
                link_elem = item.find('a', href=True)
                
                if not title_elem or not link_elem:
                    continue
                
                title = title_elem.text.strip()
                link = link_elem.get('href')
                if not link.startswith('http'):
                    link = 'https://www.immobiliare.it' + link
                
                # Prezzo
                price_elem = item.find('span', {'data-testid': 'price'})
                price_text = price_elem.text.strip() if price_elem else "0"
                price = int(''.join(filter(str.isdigit, price_text)))
                
                # Metratura
                mq = 0
                mq_elem = item.find(string=lambda x: x and 'mq' in x.lower())
                if mq_elem:
                    mq_text = mq_elem.split()[0]
                    mq = int(mq_text) if mq_text.isdigit() else 0
                
                # Camere
                rooms = 0
                text = item.get_text().lower()
                if 'trilocale' in text or 'tre locali' in text:
                    rooms = 3
                elif 'bilocale' in text:
                    rooms = 2
                elif 'quadrilocale' in text:
                    rooms = 4
                
                # Descrizione
                desc_elem = item.find('p')
                description = desc_elem.text.strip()[:100] if desc_elem else title
                
                # Zona
                zone = title.split(',')[-1].strip() if ',' in title else "Milano"
                
                # Foto
                images = []
                img_elements = item.find_all('img')
                for img in img_elements[:2]:
                    img_url = img.get('src') or img.get('data-src')
                    if img_url and 'pwm.im-cdn.it' in img_url:
                        images.append(img_url)
                
                listing = {
                    'title': title,
                    'price': price,
                    'mq': mq,
                    'rooms': rooms,
                    'zone': zone,
                    'description': description,
                    'link': link,
                    'images': images
                }
                
                # Filtra
                if price <= 400000 and mq >= 80 and rooms >= 3:
                    listings.append(listing)
                    print(f"   ✅ Aggiunto: {title[:50]}")
                
            except Exception as e:
                print(f"   ⚠️ Errore parsing: {str(e)[:50]}")
                continue
        
        return listings
        
    except Exception as e:
        print(f"   ❌ Errore scraping: {e}")
        return None

def invia_telegram(listing):
    """Invia il listing su Telegram con FOTO + LINK DIRETTO"""
    text_message = f"""🏠 <b>{listing['title']}</b>

💰 €{listing['price']:,}
📐 {listing['mq']} mq
🛏️ {listing['rooms']} camere
📍 {listing['zone']}

📝 {listing['description']}

🔗 <a href="{listing['link']}">Visualizza Annuncio</a>

⏰ {listing['timestamp']}"""
    
    try:
        # Prova ad inviare con FOTO
        if listing['images'] and len(listing['images']) > 0:
            media_group = []
            
            for idx, img_url in enumerate(listing['images'][:2]):
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
                    print(f"   ✅ Inviato con {len(media_group)} FOTO: {listing['title'][:45]}")
                    return True
                else:
                    print(f"   ⚠️ Foto fallite, provo solo testo...")
        
        # Fallback: invia SOLO TESTO con link
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': CHAT_ID,
            'text': text_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'false'
        }
        response = requests.post(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Inviato (testo + link): {listing['title'][:45]}")
            return True
        else:
            print(f"   ❌ Errore ({response.status_code})")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore invio: {str(e)[:50]}")
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
    print("🚀 BOT HOUSE FINDER MILANO - LIVE SCRAPING")
    print("=" * 70)
    print(f"⏰ Ora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📊 Modalità: SCARICA DATI REALI DA IMMOBILIARE")
    print(f"   Filtri: Prezzo max €400k, Mq min 80, Min 3 locali")
    print("=" * 70)
    
    listing_visti = carica_listing_visti()
    print(f"📚 Listing già inviati: {len(listing_visti)}\n")
    
    # Scarica i listing REALI
    listings = scrape_immobiliare()
    
    if not listings:
        print("❌ Nessun listing trovato")
        return
    
    print(f"   📄 Listing caricati: {len(listings)}\n")
    
    nuovi = 0
    for listing in listings:
        listing['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        listing_id = f"{listing['price']}_{listing['mq']}_{listing['link']}"
        
        if listing_id not in listing_visti:
            print(f"   🆕 NUOVO LISTING REALE:")
            print(f"      {listing['title'][:60]}")
            print(f"      {listing['mq']} mq | €{listing['price']:,} | {len(listing['images'])} FOTO")
            
            invia_telegram(listing)
            listing_visti.add(listing_id)
            nuovi += 1
            time.sleep(2)
    
    print()
    if nuovi > 0:
        print(f"✅ {nuovi} LISTING REALI INVIATO/I SU TELEGRAM")
        salva_listing_visti(listing_visti)
    else:
        print(f"✅ Nessun nuovo listing")
    
    print(f"\n✅ Prossima esecuzione tra 5 minuti!")

if __name__ == "__main__":
    main()
