#!/usr/bin/env python3
"""
Script principal pour le scraping avancé.

Usage:
    python main.py [--config CONFIG_PATH] [--headless] [--dry-run]
"""

import argparse
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.panel import Panel
import signal

# Ajout du chemin src pour les imports
sys.path.append(str(Path(__file__).parent / "src"))

from core.scraper import AdvancedScraper
from exporters.data_exporter import DataExporter
from utils.logger import setup_logger
from core.exceptions import ScrapingError, ConfigurationError

# Configuration du logger
logger = setup_logger("main")
console = Console()

class ScrapingApp:
    """Application principale de scraping."""
    
    def __init__(self):
        self.scraper = None
        self.interrupted = False
        
        # Gestionnaire d'interruption propre
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Gestionnaire d'interruption propre."""
        console.print("\n[yellow]⚠️  Interruption détectée - arrêt propre en cours...[/yellow]")
        self.interrupted = True
        if self.scraper and hasattr(self.scraper, 'browser_manager'):
            self.scraper.browser_manager.close()
        sys.exit(0)
    
    def display_welcome(self):
        """Affiche le message d'accueil."""
        welcome_text = """
🕷️  [bold blue]Advanced Web Scraper v2.0[/bold blue]

[dim]Un scraper robuste et éthique pour l'extraction de données web[/dim]

⚡ Fonctionnalités principales:
  • Gestion intelligente des CAPTCHAs
  • Délais adaptatifs anti-détection  
  • Export multi-formats (JSON, CSV, Excel)
  • Logging détaillé et monitoring
  • Configuration flexible via YAML
        """
        console.print(Panel(welcome_text, border_style="blue"))
    
    def display_config_summary(self, scraper: AdvancedScraper):
        """Affiche un résumé de la configuration."""
        config = scraper.config
        
        table = Table(title="📋 Configuration de scraping", show_header=True)
        table.add_column("Paramètre", style="cyan")
        table.add_column("Valeur", style="green")
        
        # Informations principales
        table.add_row("🎯 Cibles", str(len(config['targets'])))
        table.add_row("📄 Pages max/cible", str(config['scraping']['max_pages']))
        table.add_row("🕶️  Mode headless", "Oui" if config['scraping']['headless'] else "Non")
        table.add_row("⏱️  Délai min", f"{config['timing']['min_delay_between_requests']}s")
        table.add_row("⏱️  Délai max", f"{config['timing']['max_delay_between_requests']}s")
        table.add_row("🔄 Retry max", str(config['limits']['max_retries']))
        
        # Détail des cibles
        for i, target in enumerate(config['targets'], 1):
            table.add_row(
                f"   Cible {i}",
                f"{target['name']} ({len(target['keywords'])} mots-clés)"
            )
        
        console.print(table)
    
    def display_results_summary(self, ads, stats):
        """Affiche un résumé des résultats."""
        # Tableau principal
        table = Table(title="📊 Résultats du scraping", show_header=True)
        table.add_column("Métrique", style="cyan")
        table.add_column("Valeur", style="green")
        
        table.add_row("🎯 Total annonces", str(len(ads)))
        table.add_row("✅ Pages réussies", str(stats['successful_pages']))
        table.add_row("❌ Pages échouées", str(stats['failed_pages']))
        table.add_row("📊 Taux de réussite", f"{stats['success_rate']:.1f}%")
        table.add_row("🕐 Durée totale", f"{stats['duration_seconds']:.0f}s")
        table.add_row("🤖 CAPTCHAs", str(stats['captcha_encounters']))
        
        console.print(table)
        
        # Analyse des prix si disponible
        if ads:
            prices = [ad.clean_price for ad in ads if ad.clean_price and ad.clean_price > 0]
            if prices:
                console.print("\n[bold]💰 Analyse des prix:[/bold]")
                console.print(f"  • Prix moyen: {sum(prices)/len(prices):.2f}€")
                console.print(f"  • Prix médian: {sorted(prices)[len(prices)//2]:.2f}€")
                console.print(f"  • Prix min/max: {min(prices):.2f}€ - {max(prices):.2f}€")
    
    def run(self, config_path: str, dry_run: bool = False):
        """Lance l'application de scraping."""
        try:
            # Initialisation
            self.display_welcome()
            
            console.print("[yellow]🔧 Initialisation du scraper...[/yellow]")
            self.scraper = AdvancedScraper(config_path)
            
            # Affichage de la configuration
            self.display_config_summary(self.scraper)
            
            if dry_run:
                console.print("\n[blue]ℹ️  Mode dry-run activé - aucun scraping effectué[/blue]")
                return
            
            # Confirmation utilisateur
            if not console.input("\n[bold]Continuer avec le scraping ? [y/N]: [/bold]").lower().startswith('y'):
                console.print("[yellow]Scraping annulé par l'utilisateur[/yellow]")
                return
            
            # Scraping avec barre de progression
            console.print("\n[green]🚀 Début du scraping...[/green]")
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                
                task = progress.add_task("Scraping en cours...", total=100)
                
                # Lancement du scraping
                ads = self.scraper.scrape_all_targets()
                progress.update(task, completed=100)
            
            # Statistiques
            stats = self.scraper.get_session_stats()
            
            # Affichage des résultats
            console.print("\n[green]✅ Scraping terminé![/green]")
            self.display_results_summary(ads, stats)
            
            # Export des données
            if ads:
                console.print("\n[blue]💾 Export des données...[/blue]")
                exporter = DataExporter()
                
                # Export dans tous les formats
                files = exporter.export_all_formats(ads)
                
                console.print("\n[green]📁 Fichiers créés:[/green]")
                for format_type, filepath in files.items():
                    console.print(f"  • {format_type.upper()}: {filepath}")
                
                # Génération du rapport
                report = exporter.generate_report(ads, stats)
                console.print(f"\n[blue]📋 Rapport disponible dans les exports[/blue]")
            else:
                console.print("\n[yellow]⚠️  Aucune donnée à exporter[/yellow]")
            
        except ConfigurationError as e:
            console.print(f"[red]❌ Erreur de configuration: {e}[/red]")
            sys.exit(1)
        except ScrapingError as e:
            console.print(f"[red]❌ Erreur de scraping: {e}[/red]")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Scraping interrompu par l'utilisateur[/yellow]")
        except Exception as e:
            logger.exception("Erreur inattendue")
            console.print(f"[red]💥 Erreur inattendue: {e}[/red]")
            sys.exit(1)

def main():
    """Point d'entrée principal."""
    parser = argparse.ArgumentParser(
        description="Advanced Web Scraper - Solution robuste de scraping"
    )
    parser.add_argument(
        "--config", 
        default="config/config.yaml",
        help="Chemin vers le fichier de configuration (défaut: config/config.yaml)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mode test - affiche la configuration sans scraper"
    )
    parser.add_argument(
        "--headless",
        action="store_true", 
        help="Force le mode headless"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mode verbose (debug)"
    )
    
    args = parser.parse_args()
    
    # Configuration du niveau de log
    if args.verbose:
        logger.setLevel("DEBUG")
    
    # Vérification du fichier de configuration
    if not Path(args.config).exists():
        console.print(f"[red]❌ Fichier de configuration non trouvé: {args.config}[/red]")
        sys.exit(1)
    
    # Lancement de l'application
    app = ScrapingApp()
    app.run(args.config, args.dry_run)

if __name__ == "__main__":
    main()