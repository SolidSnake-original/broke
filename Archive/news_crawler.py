import pandas as pd
from newspaper import Article
from newspaper import Config
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import random
import logging
import re

# --- Logging-Setup ---
logging.basicConfig(
    filename="broker.log", 
    filemode="w", 
    format="%(asctime)s [%(levelname)s]: %(message)s", 
    level=logging.INFO
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
console.setFormatter(formatter)
logging.getLogger().addHandler(console)

# Benutzeragent zur Tarnung
USER_AGENT = random.choice([
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Mozilla/5.0 (X11; Linux x86_64)"
])
config = Config()
config.browser_user_agent = USER_AGENT
config.request_timeout = 10

# Nachrichtenseiten
news_sites = {
    "Der Standard": "https://www.derstandard.at",
    "Die Presse": "https://www.diepresse.com",
    "Kurier": "https://kurier.at"
}
kategorien = ["wirtschaft"]

granular_sites = {}
for name, url in news_sites.items():
    for k in kategorien:
        granular_sites[f"{name} {k.capitalize()}"] = f"{url}/{k}"

# 1. Pattern Matching Funktion für Artikel-Links
def is_article_url(url):
    # Nur Artikel-Links, keine Übersichtsseiten oder Hubs
    article_patterns = [
        r'/story/', r'/artikel/', r'/nachrichten/', r'/politik/', r'/wirtschaft/', r'/kultur/', r'/chronik/', r'/meinung/'
    ]
    non_article_patterns = [
        r'/autor/', r'/author/', r'/tag/', r'/thema/', r'/suche/', r'/video/'
    ]
    # Wenn der Link exakt auf eine Kategorie endet, ist es KEIN Artikel!
    for pat in article_patterns:
        # Übersichtsseiten erkennen: enden auf /pattern/ ohne weiteren Pfad oder mit nur Querystring
        if re.search(pat, url):
            path_after = url.split(pat,1)[-1]
            # Kategorie, wenn nach pattern nichts oder nur "?xyz" oder "#" folgt
            if path_after == "" or path_after.startswith("?") or path_after.startswith("#"):
                return False
            for napat in non_article_patterns:
                if re.search(napat, url):
                    return False
            return True
    return False

# 2. Link-Sammel-Funktion mit Patternfilter
def get_article_links(base_url, limit=10):
    try:
        logging.info(f"Extrahiere Artikel-Links von {base_url}...")
        response = requests.get(base_url, headers={"User-Agent": USER_AGENT}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        for a in soup.find_all('a', href=True):
            full_url = urljoin(base_url, a['href'])
            if base_url in full_url and is_article_url(full_url):
                links.append(full_url)
        unique_links = list(set(links))[:limit]
        logging.info(f"{len(unique_links)} Artikel-Links gefunden auf {base_url}.")
        return unique_links
    except Exception as e:
        logging.error(f"Fehler beim Link-Extrahieren ({base_url}): {e}")
        return []

# 3. Artikel-Zusammenfassung mit Fehlerprüfung
def summarize_articles(links):
    summaries = []
    for idx, url in enumerate(links, 1):
        if not isinstance(url, str):
            logging.warning(f"Ungültiger Link übersprungen: {url}")
            continue
        # Doppelt prüfen, ob URL wie ein Einzelartikel aussieht
        if url.rstrip('/').count('/') < 4:  # Meist sind Artikel länger verschachtelt
            logging.info(f"Übersichts- oder Kategorielink übersprungen: {url}")
            continue
        try:
            logging.info(f"[{idx}/{len(links)}] Lade Artikel: {url}")
            article = Article(url, language="de", config=config)
            article.download()
            article.parse()
            article.nlp()
            summaries.append({
                "Titel": article.title,
                "Autor(en)": ", ".join(article.authors),
                "URL": url,
                "Zusammenfassung": article.summary
            })
            logging.info(f"Artikel geladen: '{article.title}' (Autor/en: {', '.join(article.authors)})")
        except Exception as e:
            logging.warning(f"Fehler bei Artikel ({url}): {e}")
    return summaries

# --- Hauptlogik ---
if __name__ == "__main__":
    all_articles = []
    for name, base_url in granular_sites.items():
        logging.info(f"Starte Crawling für {name} ({base_url})")
        links = get_article_links(base_url, limit=10)
        articles = summarize_articles(links)
        all_articles.extend(articles)

    df = pd.DataFrame(all_articles)
    df.to_csv("artikel_und_autoren.csv", index=False, encoding='utf-8')
    logging.info("Fertig. Daten gespeichert in 'artikel_und_autoren.csv'")
