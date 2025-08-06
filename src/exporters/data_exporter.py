"""Exporteurs de données pour différents formats."""

import json
import csv
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from models.ad import Ad

logger = logging.getLogger(__name__)

class DataExporter:
    """Gestionnaire d'export des données scrapées."""
    
    def __init__(self, output_dir: str = "results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def _generate_filename(self, base_name: str, extension: str) -> str:
        """Génère un nom de fichier avec timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{base_name}_{timestamp}.{extension}"
    
    def export_json(self, ads: List[Ad], filename: str = None) -> str:
        """
        Exporte les annonces au format JSON.
        
        Args:
            ads: Liste des annonces
            filename: Nom du fichier (auto-généré si None)
            
        Returns:
            str: Chemin du fichier créé
        """
        if not filename:
            filename = self._generate_filename("scraping_results", "json")
        
        filepath = self.output_dir / filename
        
        # Préparation des données
        export_data = {
            'metadata': {
                'export_date': datetime.now().isoformat(),
                'total_ads': len(ads),
                'version': '1.0'
            },
            'ads': [ad.to_dict() for ad in ads]
        }
        
        # Export
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ Export JSON: {filepath}")
        return str(filepath)
    
    def export_csv(self, ads: List[Ad], filename: str = None) -> str:
        """
        Exporte les annonces au format CSV.
        
        Args:
            ads: Liste des annonces
            filename: Nom du fichier (auto-généré si None)
            
        Returns:
            str: Chemin du fichier créé
        """
        if not filename:
            filename = self._generate_filename("scraping_results", "csv")
        
        filepath = self.output_dir / filename
        
        if not ads:
            logger.warning("Aucune annonce à exporter")
            return str(filepath)
        
        # Conversion en DataFrame pour un export plus propre
        df = pd.DataFrame([ad.to_dict() for ad in ads])
        df.to_csv(filepath, index=False, encoding='utf-8-sig')  # BOM pour Excel
        
        logger.info(f"✅ Export CSV: {filepath}")
        return str(filepath)
    
    def export_excel(self, ads: List[Ad], filename: str = None) -> str:
        """
        Exporte les annonces au format Excel avec analyse.
        
        Args:
            ads: Liste des annonces
            filename: Nom du fichier (auto-généré si None)
            
        Returns:
            str: Chemin du fichier créé
        """
        if not filename:
            filename = self._generate_filename("scraping_results", "xlsx")
        
        filepath = self.output_dir / filename
        
        if not ads:
            logger.warning("Aucune annonce à exporter")
            return str(filepath)
        
        df = pd.DataFrame([ad.to_dict() for ad in ads])
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Feuille principale
            df.to_excel(writer, sheet_name='Annonces', index=False)
            
            # Analyse par catégorie
            if 'category' in df.columns:
                category_stats = df.groupby('category').agg({
                    'title': 'count',
                    'clean_price': ['mean', 'median', 'min', 'max']
                }).round(2)
                category_stats.to_excel(writer, sheet_name='Stats_Categories')
            
            # Analyse par mot-clé
            if 'keyword' in df.columns:
                keyword_stats = df.groupby('keyword').agg({
                    'title': 'count',
                    'clean_price': ['mean', 'median']
                }).round(2)
                keyword_stats.to_excel(writer, sheet_name='Stats_Mots_Cles')
        
        logger.info(f"✅ Export Excel: {filepath}")
        return str(filepath)
    
    def generate_report(self, ads: List[Ad], stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un rapport d'analyse des données.
        
        Args:
            ads: Liste des annonces
            stats: Statistiques de session
            
        Returns:
            Dict: Rapport complet
        """
        if not ads:
            return {'error': 'Aucune donnée à analyser'}
        
        df = pd.DataFrame([ad.to_dict() for ad in ads])
        
        # Analyse des prix
        prices = df['clean_price'].dropna()
        price_analysis = {
            'count': len(prices),
            'mean': round(prices.mean(), 2) if len(prices) > 0 else 0,
            'median': round(prices.median(), 2) if len(prices) > 0 else 0,
            'min': round(prices.min(), 2) if len(prices) > 0 else 0,
            'max': round(prices.max(), 2) if len(prices) > 0 else 0,
            'std': round(prices.std(), 2) if len(prices) > 0 else 0
        }
        
        # Top mots dans les titres
        all_titles = ' '.join(df['title'].fillna(''))
        words = all_titles.lower().split()
        word_freq = pd.Series(words).value_counts().head(10)
        
        report = {
            'summary': {
                'total_ads': len(ads),
                'scraping_duration': f"{stats.get('duration_seconds', 0):.0f}s",
                'success_rate': f"{stats.get('success_rate', 0):.1f}%",
                'captcha_encounters': stats.get('captcha_encounters', 0)
            },
            'price_analysis': price_analysis,
            'top_words': word_freq.to_dict(),
            'by_category': df.groupby('category')['title'].count().to_dict() if 'category' in df.columns else {},
            'by_keyword': df.groupby('keyword')['title'].count().to_dict() if 'keyword' in df.columns else {}
        }
        
        return report
    
    def export_all_formats(self, ads: List[Ad], base_name: str = "scraping_results") -> Dict[str, str]:
        """
        Exporte dans tous les formats disponibles.
        
        Args:
            ads: Liste des annonces
            base_name: Nom de base pour les fichiers
            
        Returns:
            Dict: Chemins des fichiers créés par format
        """
        filepaths = {}
        
        try:
            filepaths['json'] = self.export_json(ads, f"{base_name}.json")
        except Exception as e:
            logger.error(f"Erreur export JSON: {e}")
        
        try:
            filepaths['csv'] = self.export_csv(ads, f"{base_name}.csv")
        except Exception as e:
            logger.error(f"Erreur export CSV: {e}")
        
        try:
            filepaths['excel'] = self.export_excel(ads, f"{base_name}.xlsx")
        except Exception as e:
            logger.error(f"Erreur export Excel: {e}")
        
        return filepaths