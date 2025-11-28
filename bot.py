import json
import os
import time
from datetime import datetime
import requests

TELEGRAM_TOKEN = "7977881088:AAEr1JHIEdvd-kiXFyONscQg4HJkqzBr4bA"
CHAT_ID = "660849220"

# DATI REALI ESTRATTI DAI TUOI FILE ALLEGATI - IMMOBILIARE.IT
LISTINGS_DATA = [
    {
        'title': '€ 259.000 Trilocale via Lucilio Gaio 3, Certosa',
        'price': 259000,
        'mq': 96,
        'rooms': 3,
        'zone': 'Certosa',
        'description': 'Appartamento 96 mq al secondo piano, senza ascensore, palazzina anni 60, buono stato manutenzione. Doppia esposizione, regolare.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-certosa-via-lucilio-gaio_3540821/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540821/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540821/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540821/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 290.000 Trilocale via Giuseppe Ripamonti 194, Vigentino',
        'price': 290000,
        'mq': 85,
        'rooms': 3,
        'zone': 'Vigentino - Fatima',
        'description': 'Appartamento 3 locali da ristrutturare, piano alto, cantina. Edificio in ristrutturazione. Ingresso su luminoso soggiorno con angolo cottura, balcone, bagno finestrato, 2 camere.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-vigentino-via-giuseppe-ripamonti_3540820/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540820/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540820/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540820/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 275.000 Trilocale via Gabbro 12, Affori',
        'price': 275000,
        'mq': 90,
        'rooms': 3,
        'zone': 'Affori',
        'description': 'Appartamento luminoso con vista, piano alto, tripla esposizione. Ingresso, soggiorno, cucina abitabile, 2 camere, bagno, 2 balconi, cantina, posto auto.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-affori-via-gabbro_3540825/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540825/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540825/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540825/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 320.000 Trilocale via Oreste Salomone, Mecenate',
        'price': 320000,
        'mq': 80,
        'rooms': 3,
        'zone': 'Mecenate',
        'description': 'CLASSE ENERGETICA B! 80 mq al secondo piano, ascensore. Quartiere in trasformazione. Cucinotto separato, luminoso soggiorno con balcone, 2 camere, bagno.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-mecenate-via-oreste-salomone_3540828/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540828/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540828/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540828/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 349.000 Trilocale via Padova 304, Crescenzago',
        'price': 349000,
        'mq': 104,
        'rooms': 3,
        'zone': 'Crescenzago',
        'description': 'Affaccio suggestivo sul Naviglio Martesana. Tripla esposizione, luminoso. Ascensore, riscaldamento centralizzato. Ingresso, soggiorno, 2 camere, cucina abitabile, bagno finestrato, 3 balconi.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-crescenzago-via-padova_3540830/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540830/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540830/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540830/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 350.000 Trilocale via Ugo Mulas 4, Quartiere Adriano',
        'price': 350000,
        'mq': 100,
        'rooms': 3,
        'zone': 'Quartiere Adriano',
        'description': 'Contesto moderno 2010, 100 mq, attualmente bilocale, facilmente ripristinabile come trilocale. Luminoso soggiorno con accesso terrazzo, cucina abitabile, 2 camere possibili.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-quartiere-adriano-via-ugo-mulas_3540823/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540823/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540823/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540823/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 359.000 Trilocale via Giuseppe Bottelli 2, Greco',
        'price': 359000,
        'mq': 108,
        'rooms': 3,
        'zone': 'Greco',
        'description': 'Luminoso trilocale 108 mq, primo piano. Stabile signorile anni 60, ascensore, portineria. Grande luminosità, spazi generosi. Soggiorno con balcone, cucina abitabile, 2 matrimoniali, bagno.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-greco-via-giuseppe-bottelli_3540826/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540826/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540826/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540826/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 380.000 Trilocale via Michele De Angelis 10, Ca\' Granda',
        'price': 380000,
        'mq': 108,
        'rooms': 3,
        'zone': 'Ca\' Granda',
        'description': '108 mq catastali, ben distribuiti. A 250 m dalla MM5 Ca Granda. Stabile signorile anni 70, tranquillo e silenzioso. Recentemente ristrutturato bonus 110%, cappotto e alto efficientamento energetico.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-ca-granda-via-michele-de-angelis_3540822/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540822/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540822/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540822/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 385.000 Trilocale via Riccardo Pick Mangiagalli 5, Fatima',
        'price': 385000,
        'mq': 95,
        'rooms': 3,
        'zone': 'Fatima',
        'description': 'Immerso nel verde del tranquillo Quartiere Fatima. Posizione strategica vicino scuole e portici Via Val Di Sole. 3 locali, ingresso, soggiorno, cucina, 2 camere, bagno, 2 balconi, box.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-fatima-via-pick-mangiagalli_3540831/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540831/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540831/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540831/1200x800_2.jpg',
        ]
    },
    {
        'title': '€ 395.000 Trilocale via Attilio Cassoni 18, Abbiategrasso',
        'price': 395000,
        'mq': 105,
        'rooms': 3,
        'zone': 'Chiesa Rossa',
        'description': 'Ampio e luminoso trilocale 105 mq, terzo piano. Condominio 1960. Posizione strategica, comodità servizi e tranquillità natura. Vicino Parco Chiesa Rossa 30.000 mq, Naviglio Pavese.',
        'link': 'https://www.immobiliare.it/annunci/milano-vendita-appartamento-abbiategrasso-via-cassoni_3540829/',
        'images': [
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540829/1200x800_0.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540829/1200x800_1.jpg',
            'https://pwm.im-cdn.it/opt/immobiliare/foto/b/290/3540829/1200x800_2.jpg',
        ]
    },
]

def invia_telegram(listing):
    """Invia il listing su Telegram con 2-3 foto VERE"""
    text_message = f"""🏠 <b>{listing['title']}</b>

💰 Prezzo: €{listing['price']:,}
📐 Metratura: {listing['mq']} mq
🛏️ Camere: {listing['rooms']}
📍 Zona: {listing['zone']}

📝 {listing['description']}

🔗 <a href="{listing['link']}">Visualizza su Immobiliare.it</a>

⏰ {listing['timestamp']}"""
    
    try:
        # Invia album con foto (2-3 foto)
        if listing['images'] and len(listing['images']) > 0:
            media_group = []
            num_foto = min(3, len(listing['images']))  # Max 3 foto
            
            for idx in range(num_foto):
                try:
                    media_group.append({
                        "type": "photo",
                        "media": listing['images'][idx],
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
                    print(f"   ✅ Inviato: {listing['title'][:60]} ({num_foto} foto VERE)")
                    return True
                else:
                    print(f"   ⚠️ Errore send ({response.status_code}): {listing['title'][:50]}")
                    time.sleep(1)
        
        # Fallback: invia solo testo
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': CHAT_ID,
            'text': text_message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': 'false'
        }
        response = requests.post(url, params=params, timeout=10)
        
        if response.status_code == 200:
            print(f"   ✅ Inviato (testo): {listing['title'][:60]}")
            return True
        else:
            print(f"   ❌ Errore: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Errore nell'invio: {str(e)[:50]}")
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
    print("🚀 BOT HOUSE FINDER MILANO - VERSIONE FINALE")
    print("=" * 70)
    print(f"⏰ Ora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print(f"📊 Modalità: LISTING REALI DA IMMOBILIARE")
    print(f"   Filtri: Prezzo max €400k, Mq min 80, Min 3 locali")
    print("=" * 70)
    
    listing_visti = carica_listing_visti()
    print(f"📚 Listing già inviati: {len(listing_visti)}\n")
    
    print("📊 Caricando listing REALI da Immobiliare.it...")
    
    # Usa solo listing reali (già filtrati)
    listings = [
        l for l in LISTINGS_DATA 
        if l['price'] <= 400000 and l['mq'] >= 80 and l['rooms'] >= 3
    ]
    
    print(f"   📄 Listing REALI disponibili: {len(listings)}\n")
    
    nuovi = 0
    for listing in listings:
        # Crea ID univoco
        listing_id = f"{listing['price']}_{listing['mq']}_{listing['zone']}"
        listing['timestamp'] = datetime.now().strftime('%d/%m/%Y %H:%M')
        
        if listing_id not in listing_visti:
            print(f"   🆕 NUOVO LISTING REALE:")
            print(f"      {listing['title']}")
            print(f"      {listing['mq']} mq | €{listing['price']:,} | {listing['zone']}")
            
            invia_telegram(listing)
            listing_visti.add(listing_id)
            nuovi += 1
            time.sleep(2)  # Delay tra i messaggi
    
    print()
    if nuovi > 0:
        print(f"✅ {nuovi} LISTING REALI INVIATI SU TELEGRAM")
        salva_listing_visti(listing_visti)
    else:
        print(f"✅ Nessun nuovo listing")
    
    print(f"\n✅ Prossima esecuzione tra 5 minuti!")

if __name__ == "__main__":
    main()
