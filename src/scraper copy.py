
from pprint import pprint
import requests
from bs4 import BeautifulSoup
import pandas as pd

class LeboncoinScraper:
    def __init__(self, config):
        self.config = config
        self.base_url = 'https://www.leboncoin.fr/recherche'

    def scrape(self):
        annonces = []
        # Exemple simple de scraping : à adapter pour l'URL réelle
        print(f"Scraping annonces pour les catégories: {self.config['catégories']} avec mot-clé: {self.config['mot_clé']}")
        
            
        params = {
            "text": self.config.get("mot_clé", ""),
            "page": 1,
        }
        headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        response = requests.get(self.base_url, params=params, headers=headers)
        pprint(f"Chargement des annonces depuis {self.base_url} avec paramètres {params}")
        
        if response.status_code != 200:
            print(f"Erreur lors du chargement des annonces : {response.status_code}")
            return annonces

        soup = BeautifulSoup(response.text, "html.parser")

        cards = soup.find_all("a", class_="styles_adCard__2YFTi")
        if not cards:
            print("Aucune annonce trouvée avec ce sélecteur. Vérifie la structure HTML.")
            print(soup.prettify()[:2000])  # Affiche les 2000 premiers caractères du HTML pour diag.

        for card in cards:
            title_tag = card.find("p", class_="styles_title__2tZHC")
            url = "https://www.leboncoin.fr" + card.get("href", "")
            if title_tag:
                annonces.append({
                    "title": title_tag.text.strip(),
                    "url": url
                })

        return annonces