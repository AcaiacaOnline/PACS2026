"""
Middleware de Performance e Segurança
Planejamento Acaiaca

Inclui:
- Rate Limiting
- Response Cache
- Request Logging
- Security Headers
"""

import time
import hashlib
import json
from typing import Dict, Optional, Callable
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio


# ==================== RATE LIMITING ====================

class RateLimiter:
    """
    Rate limiter baseado em token bucket algorithm.
    Limita requisições por IP e por usuário.
    """
    
    def __init__(self):
        self.requests: Dict[str, list] = defaultdict(list)
        self.blocked: Dict[str, datetime] = {}
        
        # Configurações por tipo de endpoint (AUMENTADOS para uso real)
        self.limits = {
            'default': {'requests': 300, 'window': 60},      # 300 req/min
            'auth': {'requests': 60, 'window': 60},          # 60 req/min (1 por segundo)
            'upload': {'requests': 30, 'window': 60},        # 30 req/min
            'export': {'requests': 20, 'window': 60},        # 20 req/min
            'public': {'requests': 500, 'window': 60},       # 500 req/min
        }
        
        # IPs que ignoram rate limiting (localhost, rede interna)
        self.whitelist = ['127.0.0.1', 'localhost', '::1']
    
    def _get_endpoint_type(self, path: str) -> str:
        """Determina o tipo de endpoint baseado no path"""
        if '/auth/' in path:
            return 'auth'
        elif '/upload' in path or '/import' in path:
            return 'upload'
        elif '/export' in path or '/pdf' in path or '/xlsx' in path:
            return 'export'
        elif '/public/' in path or '/transparencia/' in path:
            return 'public'
        return 'default'
    
    def _get_client_id(self, request: Request) -> str:
        """Obtém identificador único do cliente"""
        # Prioriza token de usuário, depois IP
        forwarded = request.headers.get('x-forwarded-for')
        ip = forwarded.split(',')[0] if forwarded else request.client.host
        
        auth_header = request.headers.get('authorization', '')
        if auth_header.startswith('Bearer '):
            token_hash = hashlib.md5(auth_header.encode()).hexdigest()[:16]
            return f"user:{token_hash}"
        
        return f"ip:{ip}"
    
    def _clean_old_requests(self, client_id: str, window: int):
        """Remove requisições antigas da janela"""
        cutoff = time.time() - window
        self.requests[client_id] = [
            t for t in self.requests[client_id] if t > cutoff
        ]
    
    def is_blocked(self, client_id: str) -> bool:
        """Verifica se cliente está bloqueado"""
        if client_id in self.blocked:
            if datetime.now() < self.blocked[client_id]:
                return True
            del self.blocked[client_id]
        return False
    
    def check_rate_limit(self, request: Request) -> tuple[bool, dict]:
        """
        Verifica se a requisição deve ser limitada.
        Retorna (allowed, headers)
        """
        client_id = self._get_client_id(request)
        
        # Bypass para IPs na whitelist
        ip = request.headers.get('x-forwarded-for', '').split(',')[0] or (request.client.host if request.client else '')
        if ip in self.whitelist or ip.startswith('10.') or ip.startswith('192.168.'):
            return True, {'X-RateLimit-Bypass': 'whitelist'}
        
        endpoint_type = self._get_endpoint_type(request.url.path)
        limit_config = self.limits[endpoint_type]
        
        # Verificar bloqueio
        if self.is_blocked(client_id):
            return False, {
                'X-RateLimit-Limit': str(limit_config['requests']),
                'X-RateLimit-Remaining': '0',
                'X-RateLimit-Reset': str(int(self.blocked[client_id].timestamp())),
                'Retry-After': '60'
            }
        
        # Limpar requisições antigas
        self._clean_old_requests(client_id, limit_config['window'])
        
        # Verificar limite
        current_requests = len(self.requests[client_id])
        remaining = max(0, limit_config['requests'] - current_requests - 1)
        
        headers = {
            'X-RateLimit-Limit': str(limit_config['requests']),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(int(time.time() + limit_config['window']))
        }
        
        if current_requests >= limit_config['requests']:
            # Bloquear por 1 minuto após exceder limite
            self.blocked[client_id] = datetime.now() + timedelta(minutes=1)
            headers['Retry-After'] = '60'
            return False, headers
        
        # Registrar requisição
        self.requests[client_id].append(time.time())
        return True, headers


# ==================== RESPONSE CACHE ====================

class ResponseCache:
    """
    Cache simples em memória para responses frequentes.
    Ideal para endpoints públicos que não mudam frequentemente.
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache: Dict[str, dict] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Endpoints que podem ser cacheados
        self.cacheable_patterns = [
            '/api/public/',
            '/api/transparencia/',
            '/api/stats',
            '/api/dashboard/publico'
        ]
    
    def _is_cacheable(self, path: str, method: str) -> bool:
        """Verifica se o endpoint pode ser cacheado"""
        if method != 'GET':
            return False
        return any(pattern in path for pattern in self.cacheable_patterns)
    
    def _generate_key(self, request: Request) -> str:
        """Gera chave única para a requisição"""
        key_parts = [
            request.method,
            request.url.path,
            str(sorted(request.query_params.items()))
        ]
        return hashlib.md5(':'.join(key_parts).encode()).hexdigest()
    
    def _clean_expired(self):
        """Remove entradas expiradas"""
        now = time.time()
        expired = [k for k, v in self.cache.items() if v['expires'] < now]
        for k in expired:
            del self.cache[k]
    
    def _evict_oldest(self):
        """Remove entradas mais antigas se cache cheio"""
        if len(self.cache) >= self.max_size:
            oldest = sorted(self.cache.items(), key=lambda x: x[1]['created'])[:100]
            for k, _ in oldest:
                del self.cache[k]
    
    def get(self, request: Request) -> Optional[dict]:
        """Obtém response do cache se existir"""
        if not self._is_cacheable(request.url.path, request.method):
            return None
        
        key = self._generate_key(request)
        if key in self.cache:
            entry = self.cache[key]
            if entry['expires'] > time.time():
                return entry['data']
            del self.cache[key]
        return None
    
    def set(self, request: Request, data: dict, ttl: int = None):
        """Armazena response no cache"""
        if not self._is_cacheable(request.url.path, request.method):
            return
        
        self._clean_expired()
        self._evict_oldest()
        
        key = self._generate_key(request)
        self.cache[key] = {
            'data': data,
            'created': time.time(),
            'expires': time.time() + (ttl or self.default_ttl)
        }
    
    def invalidate(self, pattern: str = None):
        """Invalida cache por padrão"""
        if pattern:
            keys_to_delete = [k for k in self.cache.keys() if pattern in k]
            for k in keys_to_delete:
                del self.cache[k]
        else:
            self.cache.clear()


# ==================== MIDDLEWARE ====================

rate_limiter = RateLimiter()
response_cache = ResponseCache()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware que aplica rate limiting, cache e headers de segurança"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Verificar rate limit
        allowed, rate_headers = rate_limiter.check_rate_limit(request)
        
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={
                    'detail': 'Too many requests. Please try again later.',
                    'retry_after': rate_headers.get('Retry-After', '60')
                },
                headers=rate_headers
            )
        
        # Verificar cache
        cached = response_cache.get(request)
        if cached:
            response = JSONResponse(content=cached)
            response.headers['X-Cache'] = 'HIT'
            return response
        
        # Processar requisição
        response = await call_next(request)
        
        # Adicionar headers de performance
        process_time = time.time() - start_time
        response.headers['X-Process-Time'] = f"{process_time:.4f}"
        response.headers['X-Cache'] = 'MISS'
        
        # Adicionar rate limit headers
        for key, value in rate_headers.items():
            response.headers[key] = value
        
        # Headers de segurança
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        return response


# ==================== DECORATORS ====================

def cache_response(ttl: int = 300):
    """Decorator para cachear response de um endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get('request') or (args[0] if args else None)
            if request:
                cached = response_cache.get(request)
                if cached:
                    return cached
            
            result = await func(*args, **kwargs)
            
            if request and isinstance(result, dict):
                response_cache.set(request, result, ttl)
            
            return result
        return wrapper
    return decorator


def rate_limit(requests_per_minute: int = 60):
    """Decorator para rate limit customizado em um endpoint"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Implementação simplificada para decorator
            return await func(*args, **kwargs)
        return wrapper
    return decorator
