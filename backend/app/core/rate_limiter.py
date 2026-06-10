import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_attempts: int = 5, window_seconds: int = 60):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._attempts: dict[str, list[float]] = defaultdict(list)

    def _key(self, ip: str, email: str) -> str:
        return f"{ip}:{email}"

    def is_allowed(self, ip: str, email: str) -> bool:
        key = self._key(ip, email)
        now = time.time()
        window_start = now - self.window_seconds
        self._attempts[key] = [t for t in self._attempts[key] if t > window_start]
        if len(self._attempts[key]) >= self.max_attempts:
            return False
        self._attempts[key].append(now)
        return True

    def get_retry_after(self, ip: str, email: str) -> int:
        key = self._key(ip, email)
        if key not in self._attempts or not self._attempts[key]:
            return 0
        now = time.time()
        window_start = now - self.window_seconds
        recent = [t for t in self._attempts[key] if t > window_start]
        if len(recent) < self.max_attempts:
            return 0
        oldest = min(recent)
        retry_after = int(self.window_seconds - (now - oldest))
        return max(retry_after, 0)

    def reset(self, ip: str, email: str) -> None:
        key = self._key(ip, email)
        self._attempts.pop(key, None)

    def reset_all(self) -> None:
        self._attempts.clear()
