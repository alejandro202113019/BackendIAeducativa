import json
import hashlib
from functools import wraps
from typing import Any, Callable, Optional

from redis import Redis

from app.config import (
    REDIS_HOST, 
    REDIS_PORT, 
    REDIS_DB, 
    REDIS_PASSWORD,
    CACHE_TTL,
    REDIS_ENABLED
)

# Singleton para la conexión a Redis
_redis_client: Optional[Redis] = None

def get_redis_connection() -> Redis:
    """Obtiene una conexión a Redis (patrón Singleton)"""
    global _redis_client
    
    if not REDIS_ENABLED:
        return None
        
    if _redis_client is None:
        _redis_client = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB,
            password=REDIS_PASSWORD,
            decode_responses=True,
            socket_timeout=5,
        )
    
    return _redis_client

def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Genera una clave de caché consistente basada en los argumentos"""
    # Convertir argumentos a string y ordenar kwargs para consistencia
    args_str = str(args)
    kwargs_str = json.dumps(kwargs, sort_keys=True)
    
    # Generar hash MD5 para la clave
    key_str = f"{prefix}:{args_str}:{kwargs_str}"
    return hashlib.md5(key_str.encode()).hexdigest()

def cache_result(prefix: str, ttl: int = CACHE_TTL):
    """Decorador para cachear resultados de funciones"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Omitir caché si Redis no está habilitado
            if not REDIS_ENABLED:
                return await func(*args, **kwargs)
            
            # Obtener cliente Redis
            redis_client = get_redis_connection()
            if not redis_client:
                return await func(*args, **kwargs)
            
            # Generar clave de caché
            cache_key = generate_cache_key(prefix, *args, **kwargs)
            
            # Intentar obtener resultados de caché
            cached_result = redis_client.get(cache_key)
            if cached_result:
                try:
                    return json.loads(cached_result)
                except Exception:
                    # Si hay error al deserializar, ignorar la caché
                    pass
            
            # Ejecutar función y cachear resultado
            result = await func(*args, **kwargs)
            try:
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result)
                )
            except Exception as e:
                # Logear error pero no interrumpir el flujo
                print(f"Error al cachear resultado: {e}")
            
            return result
        return wrapper
    return decorator

def invalidate_cache(prefix: str, *args, **kwargs):
    """Invalida una entrada específica de caché"""
    if not REDIS_ENABLED:
        return
        
    redis_client = get_redis_connection()
    if not redis_client:
        return
    
    cache_key = generate_cache_key(prefix, *args, **kwargs)
    redis_client.delete(cache_key)

def clear_cache_by_pattern(pattern: str):
    """Limpia todas las entradas de caché que coincidan con un patrón"""
    if not REDIS_ENABLED:
        return
        
    redis_client = get_redis_connection()
    if not redis_client:
        return
    
    # Usar SCAN para buscar claves de manera eficiente
    cursor = 0
    while True:
        cursor, keys = redis_client.scan(cursor=cursor, match=pattern, count=100)
        if keys:
            redis_client.delete(*keys)
        if cursor == 0:
            break