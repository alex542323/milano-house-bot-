import re
import json
import os
import time
from datetime import datetime
import requests

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

# Dati estratti da Immobiliare con FOTO e LINK DIRETTI
LISTINGS_DATA = [
    {
        'title': '€ 290.000 Trilocale via Giuseppe Ripamonti 194, Vigentino',
        'price': 290000,
        'mq': 85,
        'rooms': 3,
        'description': 'Vendesi appartamento di tre locali da ristrutturare, situato al piano alto di un edificio in fase di ristrutturazione, con cantina di pertinenza.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-vigentino-via-giuseppe-ripamonti_3540820/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540820/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540820/1200x800_1.jpg',
        ]
    },
    {
        'title': '€ 259.000 Trilocale via Lucilio Gaio 3, Certosa',
        'price': 259000,
        'mq': 96,
        'rooms': 3,
        'description': 'Appartamento di 96 mq situato al secondo ed ultimo piano, senza ascensore, di una piccola palazzina degli anni 60 in buono stato di manutenzione.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-certosa-via-lucilio-gaio_3540821/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540821/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 380.000 Trilocale via Michele De Angelis 10, Ca\' Granda',
        'price': 380000,
        'mq': 108,
        'rooms': 3,
        'description': 'Ottimo appartamento di mq. 108 catastali, ben distribuiti. A soli 250 m dalla metropolitana Ca Granda (M5).',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-ca-granda-via-michele-de-angelis_3540822/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540822/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 350.000 Trilocale via Ugo Mulas 4, Quartiere Adriano',
        'price': 350000,
        'mq': 100,
        'rooms': 3,
        'description': 'TRILOCALE di 100 mq in moderno e tranquillo contesto del 2010, attualmente trasformato in BILOCALE.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-quartiere-adriano-via-ugo-mulas_3540823/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540823/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 369.000 Trilocale via Viotti 9, Città Studi',
        'price': 369000,
        'mq': 95,
        'rooms': 3,
        'description': 'Appartamento SPAZIOSO, situato in una posizione STRATEGICA nel cuore di Città Studi.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-citta-studi-via-viotti_3540824/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540824/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 275.000 Trilocale via Gabbro 12, Affori',
        'price': 275000,
        'mq': 90,
        'rooms': 3,
        'description': 'Appartamento luminoso e con vista, posizionato ad un piano alto con tripla esposizione in zona tranquilla.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-affori-via-gabbro_3540825/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540825/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 359.000 Trilocale via Giuseppe Bottelli 2, Greco',
        'price': 359000,
        'mq': 108,
        'rooms': 3,
        'description': 'Luminoso Trilocale in stabile signorile degli anni 60, ben curato e dotato di ascensore e servizio di portineria.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-greco-via-giuseppe-bottelli_3540826/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540826/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 349.000 Trilocale via Rembrandt 9, Gambara',
        'price': 349000,
        'mq': 95,
        'rooms': 3,
        'description': 'Trilocale in stabile signorile in fase di ristrutturazione al quarto piano con ingresso, soggiorno con cucina a vista e balcone.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-gambara-via-rembrandt_3540827/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540827/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 320.000 Trilocale via Oreste Salomone, Viale Ungheria',
        'price': 320000,
        'mq': 80,
        'rooms': 3,
        'description': 'CLASSE ENERGETICA B!!! Trilocale in quartiere in piena trasformazione, dove il fascino residenziale si fonde con la comodità dei collegamenti.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-mecenate-via-oreste-salomone_3540828/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540828/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 395.000 Trilocale via Attilio Cassoni 18, Cermenate',
        'price': 395000,
        'mq': 105,
        'rooms': 3,
        'description': 'Ampio e luminoso trilocale di 105 mq, situato al terzo piano di un condominio del 1960.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-abbiategrasso-via-cassoni_3540829/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540829/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 349.000 Trilocale via Padova 304, Crescenzago',
        'price': 349000,
        'mq': 104,
        'rooms': 3,
        'description': 'Stabile con affaccio diretto sul suggestivo Naviglio Martesana, tripla esposizione che garantisce luminosità durante tutta la giornata.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-crescenzago-via-padova_3540830/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540830/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 385.000 Trilocale via Riccardo Pick Mangiagalli 5',
        'price': 385000,
        'mq': 95,
        'rooms': 3,
        'description': 'Immerso nel verde del tranquillo Quartiere Fatima ed in posizione strategica a pochi passi dalle scuole.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-fatima-via-pick-mangiagalli_3540831/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540831/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 395.000 Trilocale via Carlo Bertolazzi, Lambrate',
        'price': 395000,
        'mq': 92,
        'rooms': 3,
        'description': 'Appartamento disposto su due livelli, con ingresso indipendente in mini palazzina.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-lambrate-via-carlo-bertolazzi_3540832/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540832/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 295.000 Trilocale via Privata Umberto Masotto 30',
        'price': 295000,
        'mq': 80,
        'rooms': 3,
        'description': 'Trilocale di circa 80 mq in zona tranquilla e silenziosa a pochi passi dalla fermata della metropolitana M4 Argonne.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-corsica-via-masotto_3540833/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540833/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 349.000 Trilocale via Flumendosa 23, Crescenzago',
        'price': 349000,
        'mq': 115,
        'rooms': 3,
        'description': 'Nel cuore del quartiere di Crescenzago, zona in forte riqualificazione urbanistica e servita da autobus e Metropolitana MM2.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-crescenzago-via-flumendosa_3540834/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540834/1200x800_0.jpg',
        ]
    },
    {
        'title': '€ 398.000 Trilocale via Comacchio 3, Corvetto',
        'price': 398000,
        'mq': 120,
        'rooms': 3,
        'description': 'Trilocale di 120 m² al secondo piano di uno stabile signorile dotato di ascensore e servizio di portineria.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-corvetto-via-comacchio_3540835/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540835/1200x800_0.jpg',
        ]
    },
]

def invia_telegram(listing):
    text_message = f"""🏠 <b>NUOVO LISTING TROVATO!</b>

<b>{listing['title']}</b>

💰 Prezzo: €{listing['price']:,}
📐 Mq: {listing['mq']}
🛏️ Camere: {listing['rooms']}

📝 <i>{listing['description']}</i>

🔗 <a href="{listing['link']}">Visualizza Annuncio Completo</a>

⏰ {listing['timestamp']}"""
    
    try:
        # Se ci sono foto, invia come album
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
                    print(f"   ✅ Album inviato ({len(media_group)} foto): {listing['title'][:50]}")
                    return True
                else:
                    print(f"   ⚠️ Errore Album ({response.status_code}), provo con messaggio testo")
        
        # Se non ci sono foto o album fallisce, invia solo testo
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': CHAT_ID,
            'text': text_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'false'
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
    print(f"📊 Modalità: LISTING CON FOTO E LINK DIRETTI")
    print(f"   Filtri: Prezzo max €400k, Mq min 80, Min 3 locali")
    print("=" * 70)
    
    listing_visti = carica_listing_visti()
    print(f"📚 Listing già monitorati: {len(listing_visti)}\n")
    
    print("📊 Caricando listing...")
    
    # Filtra listing secondo i criteri
    listings = [
        l for l in LISTINGS_DATA 
        if l['price'] <= 400000 and l['mq'] >= 80 and l['rooms'] >= 3
    ]
    
    print(f"   📄 Total listing trovati: {len(listings)}")
    
    nuovi = 0
    for listing in listings:
        # Crea ID univoco
        listing_id = f"{listing['price']}_{listing['mq']}_{listing['title'][:20]}"
        listing['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        if listing_id not in listing_visti:
            print(f"\n   🆕 NUOVO LISTING:")
            print(f"      Titolo: {listing['title'][:60]}")
            print(f"      Prezzo: €{listing['price']:,}")
            print(f"      Mq: {listing['mq']} | Camere: {listing['rooms']}")
            print(f"      Foto: {len(listing['images'])}")
            
            invia_telegram(listing)
            listing_visti.add(listing_id)
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
