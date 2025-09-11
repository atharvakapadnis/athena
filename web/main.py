from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
import uvicorn

from .middleware.auth import AuthMiddleware
from .middleware.caching import CacheMiddleware
from .api import dashboard, batches, rules, ai_analysis, system, auth
from .config import settings, validate_internal_deployment
from .exceptions import setup_exception_handlers

# FastAPI application instance
app = FastAPI(
    title = "Athena API",
    description = "Smart Description Iterative Improvemnet System API",
    version = "1.0.0",
    docs_url = "/api/docs" if settings.enable_docs else None,
    redoc_url = "/api/redoc" if settings.enable_docs else None,
)

# Security middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(CacheMiddleware, cache_ttl=settings.cache_ttl)
app.add_middleware(
    CORSMiddleware,
    allow_origins = settings.allowed_origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts = settings.allowed_hosts,
)

# Exception Handling
setup_exception_handlers(app)

# API routes
app.include_router(dashboard.router, prefix = "/api/dashboard", tags = ["dashboard"])
app.include_router(batches.router, prefix = "/api/batches", tags = ["batches"])
app.include_router(rules.router, prefix = "/api/rules", tags = ["rules"])
app.include_router(ai_analysis.router, prefix = "/api/ai", tags = ["ai_analysis"])
app.include_router(system.router, prefix = "/api/system", tags = ["system"])
app.include_router(auth.router, prefix = "/api/auth", tags = ["authentication"])

# Serve frontend static files
try:
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
    app.mount("/", StaticFiles(directory="web/static", html=True), name="frontend")
except Exception as e:
    print(f"Warning: Could not mount static files: {e}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "1.0.0",
        "environment": settings.environment,
        "ai_enabled": bool(settings.openai_api_key)
    }

@app.on_event("startup")
async def startup_event():
    """Startup event handler"""
    print("Starting Athena Web Interface...")
    validate_internal_deployment()
    print("Athena Web Interface ready!")

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug,
        workers=settings.workers if not settings.debug else 1
    )