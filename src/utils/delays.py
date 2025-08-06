"""Gestion intelligente des délais."""

import random
import time
from typing import Optional

class SmartDelayManager:
    """Gestionnaire de délais adaptatifs."""
    
    def __init__(self, min_delay: float = 1.0, max_delay: float = 5.0):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.consecutive_errors = 0
        self.last_request_time: Optional[float] = None
        
    def wait_between_requests(self):
        """Attend un délai approprié entre les requêtes."""
        current_time = time.time()
        
        # Calcul du délai de base avec facteur d'erreur
        base_delay = self.min_delay * (1.2 ** min(self.consecutive_errors, 5))
        base_delay = min(base_delay, self.max_delay)
        
        # Ajout d'un facteur aléatoire (±20%)
        jitter = random.uniform(0.8, 1.2)
        delay = base_delay * jitter
        
        # Respect du délai minimum depuis la dernière requête
        if self.last_request_time:
            elapsed = current_time - self.last_request_time
            remaining_delay = max(0, delay - elapsed)
            if remaining_delay > 0:
                time.sleep(remaining_delay)
        else:
            time.sleep(delay)
            
        self.last_request_time = time.time()
    
    def record_success(self):
        """Enregistre une requête réussie."""
        self.consecutive_errors = max(0, self.consecutive_errors - 1)
    
    def record_error(self):
        """Enregistre une erreur."""
        self.consecutive_errors += 1
    
    def wait_after_captcha(self, base_time: float = 30.0):
        """Attend après rencontre d'un CAPTCHA."""
        # Délai plus long après CAPTCHA avec variation
        delay = base_time + random.uniform(10, 30)
        time.sleep(delay)