# settings.py
BASE_URL = "https://www.leboncoin.fr/recherche"

# Plusieurs catégories possibles (listes)
CATEGORIES = ["27", "10"]  # Par exemple 27=Ordinateurs, 10=Immobilier (à adapter)

# Mots-clés possibles, une liste aussi (tu peux en mettre un seul)
KEYWORDS = ["ordinateur", "pc portable"]

QUERY_PARAMS = {
    "text": "ordinateur",
    "category": "27",
    "page": 1  # sera incrémenté en runtime
}

# Sélecteurs CSS pour les annonces et éléments extraits
SEL_ADS = "a[data-testid='adCard']"
SEL_TITLE = "p"  # OK si titre clairement dans un <p>, sinon adapter
SEL_PRICE = "span[data-testid='adPrice']"  # ou inspecte la variante exacte
SEL_URL = None  # None signifie utiliser href de l'élément <a>

PAGES = 5
WAIT_TIME = 2
HEADLESS = False

CHROME_BINARY_LOCATION = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"  # Chemin vers l'exécutable Chrome