from django.core.cache import cache
from django.conf import settings


def get_or_set_cache(key, callback, timeout=None):
    value = cache.get(key)
    if value is not None:
        return value
    value = callback()
    cache.set(key, value, timeout or settings.CACHE_TIMEOUT)
    return value


def delete_cache(key):
    cache.delete(key)


def clear_cache_pattern(pattern):
    try:
        from django_redis import get_redis_connection
        r = get_redis_connection("default")
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    except (ImportError, ModuleNotFoundError):
        pass


def delete_cache_prefix(prefix):
    try:
        from django_redis import get_redis_connection
        r = get_redis_connection("default")
        keys = r.keys(f"{prefix}*")
        if keys:
            r.delete(*keys)
    except (ImportError, ModuleNotFoundError):
        pass
