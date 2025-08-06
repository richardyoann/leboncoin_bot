"""Module principal de scraping."""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from urllib.parse import urlencode
import logging
from typing import List, Dict, Optional, Tuple
import yaml
import time

from models.ad import Ad, ScrapingSession
from utils.delays import SmartDelayManager
from utils.captcha_handler import CaptchaHandler
from .browser_manager import BrowserManager
from .exceptions import ScrapingError, ConfigurationError

logger = logging.getLogger(__name__)

class AdvancedScraper:
    """Scraper avancé avec gestion robuste des erreurs et des CAPTCHAs."""
    
    def __init__(self, config_path: str):
        """
        Initialise le scraper avec la configuration.
        
        Args:
            config_path: Chemin vers le fichier de configuration YAML
        """
        self.config = self._load_config(config_path)
        self.selectors = self._load_selectors()
        
        # Composants principaux
        self.browser_manager = BrowserManager(self.config['scraping'])
        self.delay_manager = SmartDelayManager(
            self.config['timing']['min_delay_between_requests'],
            self.config['timing']['max_delay_between_requests']
        )
        self.captcha_handler = CaptchaHandler(
            self.config['limits']['max_captcha_encounters']
        )
        
        # Session de scraping
        self.session = ScrapingSession()
        self.driver = None
        
    def _load_config(self, config_path: str) -> Dict:
        """Charge la configuration depuis un fichier YAML."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration chargée depuis {config_path}")
            return config
        except Exception as e:
            raise ConfigurationError(f"Erreur chargement config: {e}")
    
    def _load_selectors(self) -> Dict:
        """Charge les sélecteurs CSS."""
        try:
            with open('config/selectors.yaml', 'r', encoding='utf-8') as f:
                selectors = yaml.safe_load(f)
            return selectors['leboncoin']
        except Exception as e:
            logger.warning(f"Erreur chargement sélecteurs: {e}")
            # Sélecteurs par défaut
            return {
                'ads_container': "a[data-testid='adCard']",
                'title': "p[data-testid='adTitle']",
                'price': "span[data-testid='adPrice']",
                'location': "span[data-testid='adLocation']"
            }
    
    def _build_search_url(self, category: str, keyword: str, page: int = 1) -> str:
        """Construit l'URL de recherche."""
        base_url = self.config['scraping']['base_url']
        params = {
            'category': category,
            'text': keyword,
            'page': page
        }
        return f"{base_url}?{urlencode(params)}"
    
    def _wait_for_page_load(self, expected_element: str, timeout: int = None) -> bool:
        """Attend le chargement de la page."""
        timeout = timeout or self.config['timing']['element_wait_timeout']
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, expected_element))
            )
            return True
        except TimeoutException:
            return False
    
    def _extract_ad_data(self, ad_element) -> Optional[Ad]:
        """Extrait les données d'une annonce."""
        try:
            # Titre
            try:
                title_element = ad_element.find_element(By.CSS_SELECTOR, self.selectors['title'])
                title = title_element.text.strip()
            except NoSuchElementException:
                title = "Titre non disponible"
            
            # Prix
            try:
                price_element = ad_element.find_element(By.CSS_SELECTOR, self.selectors['price'])
                price = price_element.text.strip()
            except NoSuchElementException:
                price = "Prix non disponible"
            
            # URL
            url = ad_element.get_attribute('href') or ""
            
            # Localisation (optionnel)
            location = ""
            if 'location' in self.selectors:
                try:
                    location_element = ad_element.find_element(By.CSS_SELECTOR, self.selectors['location'])
                    location = location_element.text.strip()
                except NoSuchElementException:
                    pass
            
            return Ad(
                title=title,
                price=price,
                url=url,
                location=location
            )
            
        except Exception as e:
            logger.debug(f"Erreur extraction annonce: {e}")
            return None
    
    def _scrape_page(self, url: str, category: str, keyword: str, page_num: int) -> Tuple[List[Ad], bool]:
        """
        Scrape une page spécifique.
        
        Returns:
            Tuple[List[Ad], bool]: (liste_annonces, succès)
        """
        ads = []
        
        try:
            logger.info(f"Scraping: {keyword} (cat: {category}) - page {page_num}")
            
            # Navigation vers la page
            self.driver.get(url)
            self.delay_manager.wait_between_requests()
            
            # Vérification CAPTCHA
            captcha_detected, _ = self.captcha_handler.detect_captcha(self.driver)
            if captcha_detected:
                logger.warning("CAPTCHA détecté")
                if not self.captcha_handler.handle_captcha_manually(
                    self.driver, 
                    self.config['timing']['captcha_wait_timeout']
                ):
                    return ads, False
            
            # Vérification rate limiting
            if self.captcha_handler.detect_rate_limiting(self.driver):
                logger.warning("Rate limiting détecté - pause prolongée")
                self.delay_manager.wait_after_captcha(60)
                return ads, False
            
            # Attente du chargement
            if not self._wait_for_page_load(self.selectors['ads_container']):
                logger.warning(f"Timeout chargement page {page_num}")
                self.session.failed_pages += 1
                return ads, False
            
            # Extraction des annonces
            ad_elements = self.driver.find_elements(By.CSS_SELECTOR, self.selectors['ads_container'])
            
            if not ad_elements:
                logger.info(f"Aucune annonce trouvée page {page_num}")
                return ads, True  # Page vide = succès mais pas d'annonces
            
            for ad_element in ad_elements:
                ad_data = self._extract_ad_data(ad_element)
                if ad_data:
                    ad_data.category = category
                    ad_data.keyword = keyword
                    ad_data.page_number = page_num
                    ads.append(ad_data)
            
            logger.info(f"✓ {len(ads)} annonces extraites page {page_num}")
            self.session.successful_pages += 1
            self.delay_manager.record_success()
            
            return ads, True
            
        except WebDriverException as e:
            logger.error(f"Erreur WebDriver page {page_num}: {e}")
            self.session.errors.append(f"Page {page_num}: {str(e)}")
            self.session.failed_pages += 1
            self.delay_manager.record_error()
            return ads, False
            
        except Exception as e:
            logger.error(f"Erreur inattendue page {page_num}: {e}")
            self.session.errors.append(f"Page {page_num}: {str(e)}")
            self.session.failed_pages += 1
            return ads, False
    
    def scrape_target(self, target: Dict) -> List[Ad]:
        """Scrape toutes les pages pour une cible donnée."""
        all_ads = []
        
        category = target['category']
        target_name = target['name']
        keywords = target['keywords']
        max_pages = self.config['scraping']['max_pages']
        
        logger.info(f"🎯 Début scraping: {target_name}")
        
        for keyword in keywords:
            keyword_ads = []
            consecutive_empty_pages = 0
            max_empty_pages = 3  # Arrêt après 3 pages vides consécutives
            
            for page in range(1, max_pages + 1):
                # Vérification des limites d'erreur
                if len(self.session.errors) > self.config['limits']['max_consecutive_errors']:
                    logger.error("Trop d'erreurs consécutives - arrêt du scraping")
                    break
                
                # Vérification CAPTCHA limit
                if not self.captcha_handler.should_continue_scraping():
                    logger.error("Limite de CAPTCHAs atteinte - arrêt du scraping")
                    break
                
                url = self._build_search_url(category, keyword, page)
                page_ads, success = self._scrape_page(url, category, keyword, page)
                
                if success:
                    if page_ads:
                        keyword_ads.extend(page_ads)
                        consecutive_empty_pages = 0
                    else:
                        consecutive_empty_pages += 1
                        if consecutive_empty_pages >= max_empty_pages:
                            logger.info(f"Arrêt après {consecutive_empty_pages} pages vides pour '{keyword}'")
                            break
                else:
                    # En cas d'échec, attendre plus longtemps
                    time.sleep(10)
            
            logger.info(f"📊 Mot-clé '{keyword}': {len(keyword_ads)} annonces")
            all_ads.extend(keyword_ads)
        
        self.session.total_ads_found += len(all_ads)
        logger.info(f"✅ {target_name} terminé: {len(all_ads)} annonces")
        
        return all_ads
    
    def scrape_all_targets(self) -> List[Ad]:
        """Scrape toutes les cibles configurées."""
        all_ads = []
        
        logger.info("🚀 Début du scraping multi-cibles")
        
        try:
            with self.browser_manager as driver:
                self.driver = driver
                
                for target in self.config['targets']:
                    try:
                        target_ads = self.scrape_target(target)
                        all_ads.extend(target_ads)
                        
                        # Pause entre les cibles
                        if target != self.config['targets'][-1]:  # Pas de pause après la dernière
                            logger.info("⏸️  Pause entre les cibles...")
                            time.sleep(30)
                            
                    except Exception as e:
                        logger.error(f"Erreur cible {target['name']}: {e}")
                        continue
                
        except Exception as e:
            logger.error(f"Erreur critique: {e}")
            raise ScrapingError(f"Échec du scraping: {e}")
        
        # Statistiques finales
        logger.info(f"🎉 Scraping terminé!")
        logger.info(f"📊 Statistiques:")
        logger.info(f"📊 Statistiques:")
        logger.info(f"   • Total annonces: {len(all_ads)}")
        logger.info(f"   • Pages réussies: {self.session.successful_pages}")
        logger.info(f"   • Pages échouées: {self.session.failed_pages}")
        logger.info(f"   • Taux de réussite: {self.session.success_rate:.1f}%")
        logger.info(f"   • CAPTCHAs rencontrés: {self.captcha_handler.captcha_count}")
        logger.info(f"   • Durée: {self.session.duration:.0f}s")
        
        return all_ads
    
    def get_session_stats(self) -> Dict:
        """Retourne les statistiques de la session."""
        return {
            'total_ads': self.session.total_ads_found,
            'successful_pages': self.session.successful_pages,
            'failed_pages': self.session.failed_pages,
            'success_rate': self.session.success_rate,
            'duration_seconds': self.session.duration,
            'captcha_encounters': self.captcha_handler.captcha_count,
            'errors': self.session.errors
        }