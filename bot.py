import re
import json
import os
import time
from datetime import datetime
import requests

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

# Dati estratti da Immobiliare (già disponibili)
LISTINGS_DATA = """
- € 290.000Trilocale via Giuseppe Ripamonti 194, Vigentino - Fatima, MilanoVendesi appartamento di tre locali da ristrutturare, situato al piano alto di un edificio in fase di ristrutturazione, con cantina di pertinenza. L'immobile di circa 85 metri quadrati è composto da un ingresso che si apre su un luminoso soggiorno con angolo cottura, un balcone, bagno finestrato e due camere da letto.

- € 259.000Trilocale via Lucilio Gaio 3, Certosa, MilanoVia Lucilio Gaio n. 3, in zona Gallarate, proponiamo in vendita un appartamento di 96 mq situato al secondo ed ultimo piano, senza ascensore, di una piccola palazzina degli anni '60 in buono stato di manutenzione.

- € 380.000Trilocale via Michele De Angelis 10, Ca' Granda, MilanoGLO VALUE REAL ESTATE propone in VENDITA un ottimo appartamento di mq. 108 catastali, ben distribuiti. A soli 250 m dalla metropolitana Ca Granda (M5).

- € 350.000Trilocale via Ugo Mulas 4, Quartiere Adriano, MilanoRif. A476 – Q.re Adriano - Sogni un appartamento in una ZONA TRANQUILLA e BEN SERVITA? Abbiamo la soluzione che fa per te! In moderno e tranquillo contesto del 2010 proponiamo TRILOCALE di 100 mq attualmente trasformato in BILOCALE.

- € 369.000Trilocale via Viotti 9, Città Studi, MilanoRif: VT9VT9 - Sei alla ricerca di un appartamento SPAZIOSO, situato in una posizione STRATEGICA? Abbiamo la soluzione che fa al caso tuo! In Via Viotti 9, nel cuore di Città Studi.

- € 275.000Trilocale via Gabbro 12, Affori, MilanoSe state cercando in zona tranquilla un appartamento luminoso e con vista, questo immobile fa al caso vostro. Posizionato ad un piano alto con tripla esposizione.

- € 359.000Trilocale via Giuseppe Bottelli 2, Greco - Segnano, MilanoLuminoso Trilocale – Zona Greco, Milano Greco, vicinanze via De Marchi. In stabile signorile degli anni '60, ben curato e dotato di ascensore e servizio di portineria mezza giornata.

- € 349.000Trilocale via Rembrandt , 9, Gambara, MilanoM1 Gambara - Via Rembrandt 9. In stabile signorile in fase di ristrutturazione si vende al quarto piano trilocale composto da ingresso, soggiorno con cucina a vista e balcone.

- € 320.000Trilocale via Oreste Salomone, Viale Ungheria - Mecenate, MilanoRif: SA85P23L - !!!CLASSE ENERGETICA B!!! In un quartiere milanese in piena trasformazione, dove il fascino residenziale si fonde con la comodità dei collegamenti.

- € 395.000Trilocale via Attilio Cassoni 18, Cermenate - Abbiategrasso, MilanoProponiamo in vendita un ampio e luminoso trilocale di 105 mq in Via Cassoni, situato al terzo piano di un condominio del 1960.

- € 239.000Trilocale viale Ungheria 11, Viale Ungheria - Mecenate, MilanoCHE SIA PER LA TUA FAMIGLIA O PER UN OTTIMO INVESTIMENTO, ABBIAMO LA SOLUZIONE CHE FA AL CASO TUO!!

- € 349.000Trilocale via Padova 304, Crescenzago, MilanoRif. T12GRX – Vendita appartamento Milano, Naviglio Martesana, MM2 Crescenzago In stabile, con affaccio diretto sul suggestivo Naviglio Martesana.

- € 279.000Trilocale via Luigi Caroli 1, Ponte Nuovo, MilanoRif. A635 – PONTE NUOVO – Via Luigi Caroli, n. 1. All'interno di un contesto degli anni 60, con ascensore e cortile condominiale.

- € 385.000Trilocale via Riccardo Pick Mangiagalli 5, Vigentino - Fatima, MilanoIn VIA PICK MANGIAGALLI 5, immerso nel verde del tranquillo Quartiere Fatima ed in posizione strategica.

- € 359.000Trilocale via Ugo la Malfa 6, Quartiere Adriano, MilanoRif: A485 - Rif: A437 – Q.re Adriano – Se desideri un appartamento esclusivo e INTERAMENTE RISTRUTTURATO, questa è la soluzione giusta per te!

- € 395.000Trilocale via Carlo Bertolazzi, Lambrate, MilanoMilano, in mini palazzina, vi proponiamo appartamento disposto su due livelli, con ingresso indipendente.

- € 295.000Trilocale via Privata Umberto Masotto 30, Argonne - Corsica, MilanoRif: MAS_30 - In via Masotto 30, in una zona tranquilla e silenziosa a pochi passi dalla fermata della metropolitana M4 Argonne.

- € 349.000Trilocale via Flumendosa 23, Crescenzago, MilanoVia Flumendosa, nel cuore del quartiere di Crescenzago, zona in forte riqualificazione urbanistica.

- € 398.000Trilocale via comacchio ,3, Corvetto, MilanoIn Via Comacchio 3 Milano, proponiamo un trilocale di 120 m² al secondo piano di uno stabile signorile dotato di ascensore.

- € 335.000Quadrilocale via Mario Morgantini 20, San Siro, MilanoIn via Mario Morgantini, 20 traversa di via Rembrandt, in stabile civile ristrutturato del 1956.
"""

def parse_listings_from_text(data):
    """Estrae i listing dal testo dei dati"""
    listings = []
    
    # Pattern per trovare ogni listing
    pattern = r'- €\s*([\d\.]+)(.+?)(?=- €|\Z)'
    matches = re.findall(pattern, data, re.DOTALL)
    
    for price_str, content in matches:
        try:
            # Pulizia dei dati
            content = content.strip()
            lines = content.split('\n')
            
            # Estrai titolo (primo elemento)
            title_parts = lines[0].split(',')
            title = title_parts[0].strip() if title_parts else "N/A"
            
            # Estrai prezzo
            price = int(price_str.replace('.', ''))
            
            # Estrai indirizzo (dalla prima riga)
            address = lines[0].strip() if lines else "Milano"
            
            # Estrai metratura
            mq = 0
            mq_match = re.search(r'(\d+)\s*(?:mq|m²)', content)
            if mq_match:
                mq = int(mq_match.group(1))
            
            # Estrai camere
            rooms = 0
            if 'trilocale' in content.lower() or 'tre locali' in content.lower():
                rooms = 3
            elif 'bilocale' in content.lower() or 'due locali' in content.lower():
                rooms = 2
            elif 'monolocale' in content.lower() or 'un locale' in content.lower():
                rooms = 1
            elif 'quadrilocale' in content.lower() or 'quattro locali' in content.lower():
                rooms = 4
            
            # Estrai descrizione
            description = content[:200]
            
            # Crea ID unico
            listing_id = f"{price}_{mq}_{address[:20]}"
            
            listing = {
                'id': listing_id,
                'title': title,
                'price': price,
                'mq': mq,
                'rooms': rooms,
                'address': address,
                'description': description,
                'link': f'https://www.immobiliare.it/vendita-case/milano/',
                'images': [],
                'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M')
            }
            
            # Filtra: deve avere prezzo < 400k, mq >= 80, rooms >= 3
            if price <= 400000 and mq >= 80 and rooms >= 3:
                listings.append(listing)
                
        except Exception as e:
            print(f"   ⚠️ Errore nel parsing: {str(e)[:50]}")
            continue
    
    return listings

def invia_telegram(listing):
    text_message = f"""🏠 <b>NUOVO LISTING TROVATO!</b>

<b>{listing['title']}</b>

💰 Prezzo: €{listing['price']:,}
📐 Mq: {listing['mq']}
🛏️ Camere: {listing['rooms']}

📝 <i>{listing['description']}</i>

🔗 <a href="{listing['link']}">Visualizza su Immobiliare</a>

⏰ {listing['timestamp']}"""
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': CHAT_ID,
            'text': text_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'true'
        }
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
    print(f"📊 Modalità: PARSING DATI LOCALI")
    print(f"   Filtri: Prezzo max €400k, Mq min 80, Min 3 locali")
    print("=" * 70)
    
    listing_visti = carica_listing_visti()
    print(f"📚 Listing già monitorati: {len(listing_visti)}\n")
    
    print("📊 Parsing listing da dati locali...")
    listings = parse_listings_from_text(LISTINGS_DATA)
    print(f"   📄 Total listing trovati: {len(listings)}")
    
    nuovi = 0
    for listing in listings:
        if listing['id'] not in listing_visti:
            print(f"\n   🆕 NUOVO LISTING:")
            print(f"      Titolo: {listing['title'][:60]}")
            print(f"      Prezzo: €{listing['price']:,}")
            print(f"      Mq: {listing['mq']} | Camere: {listing['rooms']}")
            
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
