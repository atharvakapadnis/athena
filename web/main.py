from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer
import uvicorn

from .middleware.auth import AuthMiddleware
from .middleware.logging import LoggingMiddleware
from .api import dashboard, batches, rules, ai_analysis, system, websockets
from .config import settings
from .exceptions import setup_exception_handlers

# FastAPI application instance
app = FastAPI(
    title = "Athena API",
    description = "Smart Description Iterative Improvemnet System API",
    version = "1.0.0",
    docs_url = "/api/docs" if settings.environment != "production" else None,
    redoc_url = "/api/redoc" if settings.environment != "production" else None,
)

# Security middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(LoggingMiddleware)
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
app.include_router(websockets.router, prefix = "/api/ws", tags = ["websockets"])

@app.get("/api/health")
async def health_check():
    """ Health check endpoint """
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host = "0.0.0.0", port = 8000, reload=settings.debug)