from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Any, Optional
import hashlib
import json
import time
from datetime import datetime, timedelta

class CacheMiddleware(BaseHTTPMiddleware):
    """Advanced caching middleware for internal network deployment"""
    
    def __init__(self, app, cache_ttl: int = 300):  # 5 minutes default
        super().__init__(app)
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = cache_ttl
        
        # Cacheable endpoints for internal network
        self.cacheable_endpoints = {
            '/api/dashboard/summary': 60,        # Cache for 1 minute
            '/api/dashboard/real-time': 10,      # Cache for 10 seconds
            '/api/rules/active': 300,            # Cache for 5 minutes
            '/api/batches/history': 120,         # Cache for 2 minutes
            '/api/system/health': 30,            # Cache for 30 seconds
            '/api/system/stats': 60,             # Cache for 1 minute
        }

    async def dispatch(self, request: Request, call_next):
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)
        
        # Check if endpoint is cacheable
        endpoint = request.url.path
        cache_duration = self.cacheable_endpoints.get(endpoint)
        
        if not cache_duration:
            return await call_next(request)
        
        # Generate cache key
        cache_key = self._generate_cache_key(request)
        
        # Check cache
        cached_response = self._get_cached_response(cache_key, cache_duration)
        if cached_response:
            return Response(
                content=cached_response['content'],
                status_code=cached_response['status_code'],
                headers={
                    **cached_response['headers'],
                    'X-Cache': 'HIT',
                    'X-Cache-Age': str(int(time.time() - cached_response['timestamp']))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Cache successful responses
        if response.status_code == 200:
            await self._cache_response(cache_key, response)
            response.headers['X-Cache'] = 'MISS'
        
        return response

    def _generate_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        key_data = {
            'path': request.url.path,
            'query': str(request.query_params),
            'user': getattr(request.state, 'user', {}).get('username', 'anonymous')
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _get_cached_response(self, cache_key: str, cache_duration: int) -> Optional[Dict]:
        """Get cached response if still valid"""
        if cache_key not in self.cache:
            return None
        
        cached = self.cache[cache_key]
        if time.time() - cached['timestamp'] > cache_duration:
            del self.cache[cache_key]
            return None
        
        return cached

    async def _cache_response(self, cache_key: str, response: Response):
        """Cache response"""
        # Read response body
        response_body = b""
        async for chunk in response.body_iterator:
            response_body += chunk
        
        # Store in cache
        self.cache[cache_key] = {
            'content': response_body,
            'status_code': response.status_code,
            'headers': dict(response.headers),
            'timestamp': time.time()
        }
        
        # Recreate response with same body
        response.body_iterator = iter([response_body])
        
        # Clean old cache entries periodically
        if len(self.cache) > 1000:  # Limit cache size for internal deployment
            self._cleanup_cache()

    def _cleanup_cache(self):
        """Remove old cache entries"""
        current_time = time.time()
        keys_to_remove = []
        
        for key, cached in self.cache.items():
            if current_time - cached['timestamp'] > self.cache_ttl:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.cache[key]