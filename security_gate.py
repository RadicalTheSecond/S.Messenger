import time

class SecurityGate:
    def __init__(self):
        self.fails = {}
        self.max_attempts = 3
        self.lockout_duration = 10

    def is_blocked(self, ip):
        if ip not in self.fails:
            return False
        tries = self.fails[ip]
        if tries["count"] >= self.max_attempts:
            if time.time() - tries["lockout_start"] < self.lockout_duration:
                return True
            else:
                self.fails[ip] = {"count": 0, "lockout_start": 0}
                return False
                
        return False

    def register_failed_attempt(self, ip):
        if ip not in self.fails:
            self.fails[ip] = {"count": 0, "lockout_start": 0}
        self.fails[ip]["count"] += 1
        if self.fails[ip]["count"] >= self.max_attempts:
            self.fails[ip]["lockout_start"] = time.time()
            print(f"IP {ip} заблокирован из-за превышения лимита неудачных попыток.")