#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright-based scraper with a site-specific extractor for Immobiliare.it
and a debug fallback that saves/sends a snippet of the rendered HTML when
no listings are found for that site.
This file intentionally uses the literal TELEGRAM_TOKEN and CHAT_ID.
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

# === Search criteria (Sanremo) ===
MAX_PRICE = 250000
MIN_MQ = 90
MIN_ROOMS = 4

CENTRAL_KEYWORDS = [
    "centro", "corso imperatrice", "corso cavallotti", "corso matteotti",
    "corso garibaldi", "corso mombello", "corso inglesi", "via roma",
    "piazza colombo", "piazza bresca",
]

# Sites to scrape, updated to search in Sanremo
SCRAPE_LINKS = {
    'Immobiliare': 'https://www.immobiliare.it/vendita-case/sanremo/?prezzoMassimo=250000&superficieMinima=90&localiMinimo=4',
    'Idealista': 'https://www.idealista.it/vendita-case/sanremo-imperia/con-prezzo_250000?dimensione_90=on&quadrilocali-4=on&5-locali-o-piu=on',
    'Casa.it': 'https://www.casa.it/vendita/residenziale/sanremo/?prezzoMassimo=250000&superficieMinima=90&localiMinimo=4',
    'Subito': 'https://www.subito.it/annunci-liguria/vendita/appartamenti/imperia/sanremo/',
    'Tecnocasa': 'https://www.tecnocasa.it/annunci/immobili/liguria/imperia/sanremo.html?min_rooms=4',
    'Wikicasa': 'https://www.wikicasa.it/vendita/residenziale/sanremo/',
    'CaseTraPrivati': 'https://www.casetraprivati.it/vendita-case/sanremo',
}

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
]

LISTING_STORE = "listing_visti.json"
ALL_LISTINGS_STORE = "all_listings.json"
DASHBOARD_DIR = "docs"
DASHBOARD_FILE = os.path.join(DASHBOARD_DIR, "index.html")


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


def extract_rooms(text):
    m = re.search(r"(\d)\s*(?:locali|camere da letto|camere|vani)", text)
    if m:
        return int(m.group(1))
    if re.search(r"\bmonolocale\b", text):
        return 1
    if re.search(r"\bbilocale\b", text):
        return 2
    if re.search(r"\btrilocale\b", text):
        return 3
    if re.search(r"\bquadrilocale\b", text):
        return 4
    if re.search(r"\bpentalocale\b|\bcinque locali\b", text):
        return 5
    return 0


def is_central_zone(text):
    t = (text or "").lower()
    return any(k in t for k in CENTRAL_KEYWORDS)


def extract_for_immobiliare(html, base_url, max_items=8):
    """
    Site-specific heuristics for immobiliare.it:
    - find anchors with URLs that likely point to property pages
    - search within parent container for price/mq/rooms
    - returns list of listings
    """
    soup = BeautifulSoup(html, "html.parser")
    results = []
    # find candidate anchors that likely link to listings
    anchors = soup.find_all("a", href=True)
    seen_hrefs = set()
    for a in anchors:
        href = a["href"]
        # heuristics: immobiliare listing URLs frequently contain '/immobile/' or '/vendita-' or '/annunci/'
        if re.search(r"/immobile/|/vendita-|/annunci/|/case-in-vendita/", href, re.I):
            if href in seen_hrefs:
                continue
            seen_hrefs.add(href)
            # try to find the nearest container with textual info
            parent = a.find_parent(["article", "div", "li"]) or a
            text = parent.get_text(" ", strip=True).lower()
            # price
            price = 0
            m_price = re.search(r"€\s?([\d\.\s,]+)", parent.get_text(" ", strip=True))
            if m_price:
                digits = re.sub(r"[^\d]", "", m_price.group(1))
                if digits:
                    price = int(digits)
            # mq
            mq = 0
            m_mq = re.search(r"(\d{2,4})\s?m(?:q|²|2|q)", text)
            if m_mq:
                mq = int(m_mq.group(1))
            rooms = extract_rooms(text)
            # zone
            zone = "Sanremo"
            zn = parent.find(lambda t: t.name in ["span", "div"] and re.search(r"sanremo|san remo", t.get_text("", strip=True), re.I))
            if zn:
                zone = zn.get_text(" ", strip=True)
            link = normalize_link(href, base_url)
            if price and price <= MAX_PRICE and mq >= MIN_MQ and rooms >= MIN_ROOMS:
                title = a.get_text(" ", strip=True) or parent.get_text(" ", strip=True)[:200]
                results.append({
                    "title": title[:200],
                    "price": price,
                    "mq": mq,
                    "rooms": rooms,
                    "zone": zone,
                    "central": is_central_zone(text + " " + zone),
                    "description": title[:250],
                    "link": link,
                    "source": "Immobiliare"
                })
            if len(results) >= max_items:
                break

    # fallback: page-wide regex scan
    if not results:
        snippets = re.findall(r"(.{0,120}€[\d\.\s,]{1,30}.{0,120}mq.{0,120})", html, flags=re.I | re.S)
        for s in snippets[:max_items]:
            m_p = re.search(r"€\s?([\d\.\s,]+)", s)
            m_m = re.search(r"(\d{2,4})\s?m(?:q|²|2|q)", s)
            if m_p and m_m:
                price = int(re.sub(r"[^\d]", "", m_p.group(1)))
                mq = int(m_m.group(1))
                rooms = extract_rooms(s.lower())
                if price <= MAX_PRICE and mq >= MIN_MQ and rooms >= MIN_ROOMS:
                    results.append({
                        "title": s[:120],
                        "price": price,
                        "mq": mq,
                        "rooms": rooms,
                        "zone": "Sanremo",
                        "central": is_central_zone(s),
                        "description": s[:200],
                        "link": "",
                        "source": "Immobiliare"
                    })
    return results


def extract_listings_from_html(html, site_name, base_url, max_items=6):
    """
    General extractor; delegates to a site-specific extractor for Immobiliare
    """
    # site-specific path
    if site_name == "Immobiliare":
        return extract_for_immobiliare(html, base_url, max_items=max_items)

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

    if not items:
        items = soup.find_all("a", href=True)

    for item in items[:max_items]:
        try:
            a = item.find("a", href=True) or (item if item.name == "a" else None)
            href = a.get("href") if a else (item.get("href") if hasattr(item, "get") else "")
            link = normalize_link(href, base_url)
            title = (a.get("title") if a else "") or (a.get_text(" ", strip=True) if a else item.get_text(" ", strip=True))
            text = item.get_text(" ", strip=True).lower()
            # price
            price = 0
            price_elem = item.find(lambda tag: tag.name in ["span", "div"] and re.search(r"€|\beuro", tag.get_text("", strip=True).lower()))
            ptxt = price_elem.get_text("", strip=True) if price_elem else text
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
            rooms = extract_rooms(text)
            zone = "Sanremo"
            zn = item.find(lambda t: t.name in ["span", "div"] and re.search(r"sanremo|san remo", t.get_text("", strip=True), re.I))
            if zn:
                zone = zn.get_text(" ", strip=True)
            if price and price <= MAX_PRICE and mq >= MIN_MQ and rooms >= MIN_ROOMS:
                results.append({
                    "title": title[:200],
                    "price": price,
                    "mq": mq,
                    "rooms": rooms,
                    "zone": zone,
                    "central": is_central_zone(text + " " + zone),
                    "description": title[:250],
                    "link": link,
                    "source": site_name
                })
        except Exception:
            continue

    # fallback page-wide regex
    if not results:
        snippets = re.findall(r"(.{0,120}€[\d\.\s,]{1,30}.{0,120}mq.{0,120})", html, flags=re.I | re.S)
        for s in snippets[:max_items]:
            m_p = re.search(r"€\s?([\d\.\s,]+)", s)
            m_m = re.search(r"(\d{2,4})\s?m(?:q|²|2|q)", s)
            if m_p and m_m:
                price = int(re.sub(r"[^\d]", "", m_p.group(1)))
                mq = int(m_m.group(1))
                rooms = extract_rooms(s.lower())
                if price <= MAX_PRICE and mq >= MIN_MQ and rooms >= MIN_ROOMS:
                    results.append({
                        "title": s[:120],
                        "price": price,
                        "mq": mq,
                        "rooms": rooms,
                        "zone": "Sanremo",
                        "central": is_central_zone(s),
                        "description": s[:200],
                        "link": "",
                        "source": site_name
                    })
    return results


def send_telegram(listing):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    central_tag = " 📍centro" if listing.get("central") else ""
    text_message = (
        f"{listing['title']}\n\n"
        f"€{listing['price']:,} | {listing['mq']} mq | {listing['rooms']} locali{central_tag}\n"
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


def scrape_with_playwright(url, headless=True, timeout=40000):
    ua = random.choice(USER_AGENTS)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=ua, locale="it-IT")
        page = context.new_page()
        try:
            page.set_viewport_size({"width": 1280, "height": 900})
            page.goto(url, wait_until="networkidle", timeout=timeout)
            # small wait for late-loaded sections
            time.sleep(random.uniform(2.0, 4.0))
            # accept cookie banners if present
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


def save_and_send_debug(html, site_name):
    """
    Save HTML to file and send a short snippet to Telegram so you can inspect
    what the page looks like after JS runs.
    """
    fn = f"debug_{site_name.lower()}.html"
    try:
        with open(fn, "w", encoding="utf-8") as f:
            f.write(html)
    except Exception:
        pass
    snippet = html[:2000].replace("\n", " ")
    try:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                      json={"chat_id": CHAT_ID, "text": f"DEBUG {site_name} snippet:\n{snippet}", "disable_web_page_preview": True}, timeout=10)
    except Exception as e:
        print("Failed to send debug snippet:", e)


def make_lid(listing):
    return f"{listing.get('price','0')}_{listing.get('mq','0')}_{listing.get('link','')}"


def load_json_store(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_json_store(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_dashboard(listings):
    """Render a static, self-contained HTML dashboard with all known listings."""
    os.makedirs(DASHBOARD_DIR, exist_ok=True)
    sorted_listings = sorted(listings, key=lambda x: x.get("price", 10**12))
    data_json = json.dumps(sorted_listings, ensure_ascii=False)
    generated_at = datetime.now().strftime("%d/%m/%Y %H:%M")
    sources = sorted({l.get("source", "") for l in sorted_listings})
    source_options = "\n".join(f'<option value="{s}">{s}</option>' for s in sources)

    html = f"""<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Case in vendita a Sanremo</title>
<style>
  :root {{ color-scheme: light dark; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 0 1rem 2rem; background: #f5f5f2; color: #1a1a1a; }}
  @media (prefers-color-scheme: dark) {{ body {{ background: #14161a; color: #eee; }} .card {{ background: #1f2228 !important; border-color: #333 !important; }} input, select {{ background: #22252b; color: #eee; border-color: #444 !important; }} }}
  header {{ padding: 1.5rem 0 1rem; }}
  h1 {{ margin: 0 0 .25rem; font-size: 1.5rem; }}
  .meta {{ opacity: .7; font-size: .85rem; }}
  .filters {{ display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }}
  .filters input, .filters select {{ padding: .4rem .6rem; border: 1px solid #ccc; border-radius: 6px; font-size: .9rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1rem; }}
  .card {{ background: #fff; border: 1px solid #e0e0dc; border-radius: 10px; padding: 1rem; display: flex; flex-direction: column; gap: .4rem; }}
  .card h3 {{ margin: 0; font-size: 1rem; line-height: 1.3; }}
  .price {{ font-size: 1.2rem; font-weight: 700; }}
  .badges {{ display: flex; gap: .4rem; flex-wrap: wrap; }}
  .badge {{ font-size: .75rem; padding: .15rem .5rem; border-radius: 999px; background: #eee; }}
  .badge.central {{ background: #d7f0dc; color: #1a5c2a; }}
  @media (prefers-color-scheme: dark) {{ .badge {{ background: #333; }} .badge.central {{ background: #1a5c2a; color: #d7f0dc; }} }}
  a.link {{ margin-top: auto; text-decoration: none; color: #0b5fff; font-weight: 600; font-size: .9rem; }}
  .empty {{ opacity: .7; padding: 2rem 0; text-align: center; }}
</style>
</head>
<body>
<header>
  <h1>🏠 Case in vendita a Sanremo</h1>
  <div class="meta">Aggiornato il {generated_at} · criteri: max €{MAX_PRICE:,} · min {MIN_MQ} mq · min {MIN_ROOMS} locali · {len(sorted_listings)} annunci trovati</div>
</header>
<div class="filters">
  <input id="q" type="search" placeholder="Cerca nel titolo/zona...">
  <select id="source"><option value="">Tutte le fonti</option>{source_options}</select>
  <input id="maxPrice" type="number" placeholder="Prezzo max €">
  <input id="minMq" type="number" placeholder="Mq minimi">
  <label style="display:flex;align-items:center;gap:.3rem;"><input id="onlyCentral" type="checkbox"> Solo zona centrale</label>
</div>
<div id="grid" class="grid"></div>
<div id="empty" class="empty" style="display:none;">Nessun annuncio corrisponde ai filtri.</div>

<script>
const DATA = {data_json};

function render() {{
  const q = document.getElementById('q').value.toLowerCase();
  const source = document.getElementById('source').value;
  const maxPrice = parseFloat(document.getElementById('maxPrice').value) || Infinity;
  const minMq = parseFloat(document.getElementById('minMq').value) || 0;
  const onlyCentral = document.getElementById('onlyCentral').checked;

  const filtered = DATA.filter(l => {{
    if (source && l.source !== source) return false;
    if (l.price > maxPrice) return false;
    if (l.mq < minMq) return false;
    if (onlyCentral && !l.central) return false;
    if (q && !((l.title||'') + ' ' + (l.zone||'')).toLowerCase().includes(q)) return false;
    return true;
  }});

  const grid = document.getElementById('grid');
  grid.innerHTML = '';
  document.getElementById('empty').style.display = filtered.length ? 'none' : 'block';

  for (const l of filtered) {{
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
      <div class="badges">
        <span class="badge">${{l.source || ''}}</span>
        ${{l.central ? '<span class="badge central">📍 Centro</span>' : ''}}
      </div>
      <h3>${{(l.title || '').replace(/</g,'&lt;')}}</h3>
      <div class="price">€${{(l.price||0).toLocaleString('it-IT')}}</div>
      <div>${{l.mq||0}} mq · ${{l.rooms||0}} locali · ${{l.zone||''}}</div>
      <a class="link" href="${{l.link||'#'}}" target="_blank" rel="noopener">Vedi annuncio →</a>
    `;
    grid.appendChild(card);
  }}
}}

['q','source','maxPrice','minMq','onlyCentral'].forEach(id => {{
  document.getElementById(id).addEventListener('input', render);
}});
render();
</script>
</body>
</html>
"""
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)


def main():
    print("=" * 60)
    print("Playwright scraper run -", datetime.now().isoformat())
    print("=" * 60)
    all_listings = []
    for site_name, url in SCRAPE_LINKS.items():
        print("Loading", site_name, "...")
        html = scrape_with_playwright(url, headless=True)
        base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        listings = extract_listings_from_html(html, site_name, base_url)
        print(f"  {site_name}: extracted {len(listings)} listings")
        # if Immobiliare and nothing extracted, save/send debug snippet
        if site_name == "Immobiliare" and not listings:
            print("  Immobiliare extraction returned 0 — saving and sending debug snippet.")
            save_and_send_debug(html, "Immobiliare")
        all_listings.extend(listings)
        time.sleep(random.uniform(1.0, 3.0))

    now_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    # Persist every matching listing ever seen, so the dashboard keeps
    # showing them even if a later page load doesn't re-list them.
    store = load_json_store(ALL_LISTINGS_STORE)
    for l in all_listings:
        lid = make_lid(l)
        entry = store.get(lid, {})
        entry.update(l)
        entry.setdefault("first_seen", now_str)
        entry["last_seen"] = now_str
        store[lid] = entry
    save_json_store(ALL_LISTINGS_STORE, store)
    build_dashboard(list(store.values()))

    if not all_listings:
        print("No listings found this run.")
        return

    all_listings.sort(key=lambda x: x.get("price", 10**12))
    top = all_listings[:5]
    sent = 0
    seen = set(load_json_store(LISTING_STORE)) if os.path.exists(LISTING_STORE) else set()
    if isinstance(seen, dict):
        seen = set(seen)

    for l in top:
        l["timestamp"] = now_str
        lid = make_lid(l)
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
    print(f"Done. Sent {sent} new listings. Dashboard: {DASHBOARD_FILE} ({len(store)} total listings tracked).")


if __name__ == "__main__":
    main()
