from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Optional
import jwt
from datetime import datetime, timedelta

from ..config import settings
from ..models.user import User

security = HTTPBearer()

class AuthMiddleware(BaseHTTPMiddleware):
    """ Authentication middlware for API endpoints """
    async def dispatch(self, request: Request, call_next):
        # Skip authentication for health check and public endpoints
        if request.url.path in ["/api/health", "/api/docs", "/api/redoc"]:
            return await call_next(request)

        # Skip authentication for static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)

        # Implementing simple token based authentication
        # TODO: Integrate with current auth system
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                # validate token TODO:update logic here
                user = validate_token(token)
                request.state.user = user
            except Exception:
                pass # Continue without user for now

        return await call_next(request)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """ Create a JWT access token """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes = 15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm = "HS256")
    return encoded_jwt

def validate_token(token: str) -> User:
    """ Validate a JWT access token """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms = ["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code = 401, detail = "Invalid token")
        return User(username = username)
    except jwt.PyJWTError:
        raise HTTPException(status_code = 401, detail = "Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """ Get the current user from the token """
    return validate_token(credentials.credentials)