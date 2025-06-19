"""
Gestionnaire de limite de taux pour l'API Google Generative AI
"""

import time
import sys
import os
from datetime import datetime, timedelta

# Ajouter le répertoire parent au path pour les imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config import MAX_REQUESTS_PER_MINUTE, TIME_WINDOW


class AIRateLimiter:
    """
    Gère les limites de taux pour les requêtes API
    """
    
    def __init__(self, max_requests=MAX_REQUESTS_PER_MINUTE, time_window=TIME_WINDOW):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self):
        """
        Vérifie si une nouvelle requête peut être faite
        """
        now = datetime.now()
        # Nettoyer les anciennes requêtes
        self.requests = [
            req_time for req_time in self.requests 
            if now - req_time < timedelta(seconds=self.time_window)
        ]
        return len(self.requests) < self.max_requests
    
    def make_request(self):
        """
        Enregistre une nouvelle requête si possible
        """
        if self.can_make_request():
            self.requests.append(datetime.now())
            return True
        return False
    
    def wait_time(self):
        """
        Calcule le temps d'attente nécessaire avant la prochaine requête
        """
        if not self.requests:
            return 0
        oldest_request = min(self.requests)
        return max(0, self.time_window - (datetime.now() - oldest_request).seconds)
    
    def wait_if_needed(self):
        """
        Attend si nécessaire avant de permettre une nouvelle requête
        """
        if not self.can_make_request():
            wait_time = self.wait_time()
            print(f"Limite API atteinte. Attente de {wait_time} secondes...")
            time.sleep(wait_time + 1)
