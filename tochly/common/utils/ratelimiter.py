from django.core.cache import cache

class CacheRateLimiter:
    def __init__(self, key_prefix, limit=5, window=300):
        self.key_prefix = key_prefix
        self.limit = limit
        self.window = window

    def is_limited(self, user_id):
        key = f'{self.key_prefix}:{user_id}'
        added = cache.add(key, 1, timeout=self.window)

        if added:
            return False

        current = cache.incr(key)
        if current > self.limit:
            return True

        return False
