"""Modèles de données pour les annonces."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import re

@dataclass
class Ad:
    """Représente une annonce scrapée."""
    
    title: str
    price: str
    url: str
    location: str = ""
    category: str = ""
    keyword: str = ""
    page_number: int = 0
    scraped_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Post-traitement des données après initialisation."""
        self.clean_price = self._extract_numeric_price()
        self.title = self.title.strip() if self.title else "Titre non disponible"
        
    def _extract_numeric_price(self) -> Optional[float]:
        """Extrait le prix numérique de la chaîne de prix."""
        if not self.price or self.price.lower() in ['gratuit', 'free', 'à débattre']:
            return 0.0
            
        # Recherche de nombres avec espaces, virgules ou points
        price_pattern = r'[\d\s,.]+(?=\s*€|\s*EUR|\s*$)'
        match = re.search(price_pattern, self.price.replace(' ', ''))
        
        if match:
            price_str = match.group().replace(' ', '').replace(',', '.')
            try:
                return float(price_str)
            except ValueError:
                return None
        return None
    
    def to_dict(self) -> dict:
        """Convertit l'annonce en dictionnaire."""
        return {
            'title': self.title,
            'price': self.price,
            'clean_price': self.clean_price,
            'url': self.url,
            'location': self.location,
            'category': self.category,
            'keyword': self.keyword,
            'page_number': self.page_number,
            'scraped_at': self.scraped_at.isoformat()
        }

@dataclass
class ScrapingSession:
    """Informations sur une session de scraping."""
    
    start_time: datetime = field(default_factory=datetime.now)
    total_ads_found: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    captcha_encounters: int = 0
    errors: list = field(default_factory=list)
    
    @property
    def duration(self) -> float:
        """Durée de la session en secondes."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Taux de réussite en pourcentage."""
        total = self.successful_pages + self.failed_pages
        return (self.successful_pages / total * 100) if total > 0 else 0