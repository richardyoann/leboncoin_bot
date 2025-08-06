"""Gestionnaire du navigateur et des sessions Selenium."""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class BrowserManager:
    """Gestionnaire pour les instances de navigateur."""
    
    def __init__(self, config: dict):
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self._setup_complete = False
    
    def _create_chrome_options(self) -> Options:
        """Crée les options Chrome optimisées."""
        options = Options()
        
        # Configuration de base
        if self.config.get('headless', False):
            options.add_argument("--headless=new")
            
        # Options de performance et sécurité
        performance_args = [
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",  # Plus rapide
            "--window-size=1920,1080",
            "--disable-web-security",
            "--allow-running-insecure-content",
            "--ignore-certificate-errors",
            "--disable-infobars",            
            "--disable-popup-blocking", 
            "--allow-insecure-localhost"  
        ]
        
        for arg in performance_args:
            options.add_argument(arg)
        
        # User agent personnalisé
        if user_agent := self.config.get('user_agent'):
            options.add_argument(f"--user-agent={user_agent}")
            
        # Options expérimentales pour éviter la détection
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Prefs pour optimiser les performances
        options.add_experimental_option("prefs", {
            "profile.default_content_setting_values": {
                "images": 2,  # Bloquer les images
                "plugins": 2,
                "popups": 2,
                "geolocation": 2,
                "notifications": 2,
                "media_stream": 2,
            }
        })
        
        return options
    
    def start(self) -> webdriver.Chrome:
        """Démarre une nouvelle instance de navigateur."""
        if self.driver:
            logger.warning("Le navigateur est déjà démarré")
            return self.driver
            
        try:
            options = self._create_chrome_options()
            service = Service(ChromeDriverManager().install())
            
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Configuration post-démarrage
            self.driver.set_page_load_timeout(self.config.get('page_load_timeout', 30))
            self.driver.implicitly_wait(self.config.get('implicit_wait', 10))
            
            # Masquer les traces d'automatisation
            self.driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            
            logger.info("Navigateur démarré avec succès")
            self._setup_complete = True
            return self.driver
            
        except Exception as e:
            logger.error(f"Erreur lors du démarrage du navigateur: {e}")
            raise WebDriverException(f"Impossible de démarrer le navigateur: {e}")
    
    def is_alive(self) -> bool:
        """Vérifie si le navigateur est encore actif."""
        if not self.driver:
            return False
        try:
            self.driver.current_url
            return True
        except WebDriverException:
            return False
    
    def restart(self) -> webdriver.Chrome:
        """Redémarre le navigateur."""
        logger.info("Redémarrage du navigateur...")
        self.close()
        return self.start()
    
    def close(self):
        """Ferme le navigateur proprement."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Navigateur fermé")
            except Exception as e:
                logger.warning(f"Erreur lors de la fermeture: {e}")
            finally:
                self.driver = None
                self._setup_complete = False
    
    def __enter__(self):
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()