"""Gestionnaire de détection et traitement des CAPTCHAs."""

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CaptchaHandler:
    """Gestionnaire pour la détection et le traitement des CAPTCHAs."""
    
    CAPTCHA_SELECTORS = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']", 
        "div[class*='captcha']",
        "div[id*='captcha']",
        ".cf-browser-verification",
        "#challenge-form",
        "[data-testid*='captcha']"
    ]
    
    RATE_LIMIT_INDICATORS = [
        "trop de requêtes",
        "rate limit",
        "temporairement indisponible",
        "429",
        "service unavailable"
    ]
    
    def __init__(self, max_captcha_encounters: int = 5):
        self.max_captcha_encounters = max_captcha_encounters
        self.captcha_count = 0
        
    def detect_captcha(self, driver) -> Tuple[bool, Optional[str]]:
        """
        Détecte la présence d'un CAPTCHA.
        
        Returns:
            Tuple[bool, Optional[str]]: (captcha_detected, selector_found)
        """
        for selector in self.CAPTCHA_SELECTORS:
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                if element.is_displayed():
                    logger.warning(f"CAPTCHA détecté avec sélecteur: {selector}")
                    return True, selector
            except NoSuchElementException:
                continue
        return False, None
    
    def detect_rate_limiting(self, driver) -> bool:
        """Détecte si la page indique une limitation de taux."""
        try:
            page_text = driver.page_source.lower()
            for indicator in self.RATE_LIMIT_INDICATORS:
                if indicator in page_text:
                    logger.warning(f"Limitation de taux détectée: {indicator}")
                    return True
        except Exception as e:
            logger.debug(f"Erreur lors de la détection de rate limiting: {e}")
        return False
    
    def handle_captcha_manually(self, driver, timeout: int = 300) -> bool:
        """
        Gère un CAPTCHA en attendant une résolution manuelle.
        
        Args:
            driver: WebDriver instance
            timeout: Temps maximum d'attente en secondes
            
        Returns:
            bool: True si le CAPTCHA a été résolu, False sinon
        """
        self.captcha_count += 1
        
        if self.captcha_count > self.max_captcha_encounters:
            logger.error(f"Trop de CAPTCHAs rencontrés ({self.captcha_count}). Arrêt.")
            return False
        
        logger.info(f"CAPTCHA détecté ({self.captcha_count}/{self.max_captcha_encounters})")
        logger.info("Veuillez résoudre le CAPTCHA manuellement dans le navigateur.")
        
        try:
            # Attend que les éléments d'annonces soient présents (CAPTCHA résolu)
            WebDriverWait(driver, timeout).until(
                lambda d: not self.detect_captcha(d)[0]
            )
            logger.info("CAPTCHA résolu avec succès!")
            return True
            
        except TimeoutException:
            logger.error(f"Timeout après {timeout}s - CAPTCHA non résolu")
            return False
    
    def should_continue_scraping(self) -> bool:
        """Détermine si le scraping peut continuer."""
        return self.captcha_count <= self.max_captcha_encounters