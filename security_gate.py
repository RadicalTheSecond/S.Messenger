import time

class SecurityGate:
    def __init__(self):
        self.failed_attempts = {}
        self.max_attempts = 3
        self.lockout_duration = 10

    def is_blocked(self, ip):
        if ip not in self.failed_attempts:
            return False
        data = self.failed_attempts[ip]
        if data["count"] >= self.max_attempts:
            current_time = time.time()
            if current_time - data["lockout_start"] < self.lockout_duration:
                return True
            else:
                self.failed_attempts[ip] = {"count": 0, "lockout_start": 0}
                return False
                
        return False

    def register_failed_attempt(self, ip):
        if ip not in self.failed_attempts:
            self.failed_attempts[ip] = {"count": 0, "lockout_start": 0}
        self.failed_attempts[ip]["count"] += 1
        if self.failed_attempts[ip]["count"] >= self.max_attempts:
            self.failed_attempts[ip]["lockout_start"] = time.time()
            print(f"IP {ip} заблокирован из-за превышения лимита неудачных попыток.")