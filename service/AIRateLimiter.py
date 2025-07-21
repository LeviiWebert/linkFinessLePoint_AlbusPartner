# Gestion des limites API (15 requêtes par minute pour Gemini 1.5 Flash)
class AIRateLimiter:
    def __init__(self, max_requests=100, time_window=10):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    def can_make_request(self):
        now = datetime.now()
        # Nettoyer les anciennes requêtes
        self.requests = [req_time for req_time in self.requests if now - req_time < timedelta(seconds=self.time_window)]
        return len(self.requests) < self.max_requests
    
    def make_request(self):
        if self.can_make_request():
            self.requests.append(datetime.now())
            return True
        return False
    
    def wait_time(self):
        if not self.requests:
            return 0
        oldest_request = min(self.requests)
        return max(0, self.time_window - (datetime.now() - oldest_request).seconds)