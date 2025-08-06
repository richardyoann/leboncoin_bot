"""Exceptions personnalisées pour le scraper."""

class ScrapingError(Exception):
    """Exception de base pour les erreurs de scraping."""
    pass

class ConfigurationError(ScrapingError):
    """Erreur de configuration."""
    pass

class CaptchaError(ScrapingError):
    """Erreur liée aux CAPTCHAs."""
    pass

class RateLimitError(ScrapingError):
    """Erreur de limitation de taux."""
    pass

class BrowserError(ScrapingError):
    """Erreur du navigateur."""
    pass