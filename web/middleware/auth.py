import json
import hashlib
from pathlib import Path
from typing import Optional

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import jwt
from datetime import datetime, timedelta

from ..config import settings
from ..models.user import User

security = HTTPBearer()

# User storage fiel for internal network
USERS_FILE = Path("data/users.json")

class AuthMiddleware(BaseHTTPMiddleware):
    """ Authentication middleware for internal network API endpoints """
    async def dispatch(self, request: Request, call_next):
        #Skip authentication for health check, docs and auth endpoints
        if request.url.path in ["/api/health", "/api/docs", "/api/redoc", "/api/auth/login", "/api/auth/register"]:
            return await call_next(request)

        # Skip authentication for static files
        if request.url.path.startswith("/static/"):
            return await call_next(request)

        # Skip authentication for root path
        if request.url.path == "/":
            return await call_next(request)
        
        # Implementing simple token based authentication
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                user = validate_token(token)
                request.state.user = user
            except Exception as e:
                pass # contiue wihtout user for now

        return await call_next(request)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """ Create a JWT access token """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def hash_password(password:str) -> str:
    """ Simple password hashing for internal use """
    return hashlib.sha256(password.encode()).hexdigest()

def load_users() -> dict:
    """ Load users from JSON file """
    if not USERS_FILE.exists():
        USERS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
        return {}

    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except(json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users: dict):
    """ Save users to JSON file """
    USERS_FILE.parent.mkdir(parents= True, exist_ok=True)
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent= 2, default=str)

def authenticate_user(username: str, password:str) -> bool:
    """Authenticate user credentials"""
    users = load_users()
    user = users.get(username)
    if not user:
        return False

    return user["password"] == hash_password(password) and user.get("active", True)

def create_user(username: str, email: str, password: str, role: str = "user") -> User:
    """ Create a new user """
    users = load_users()

    if username in  users:
        raise HTTPException(status_code=400, detail="Username already exists")

    # If not users exists, first user becomes admin
    is_first_user = len(users) == 0
    actual_role = "admin" if is_first_user else role

    new_user_data = {
        "username": username,
        "email": email,
        "password": hash_password(password),
        "role": actual_role,
        "active": True,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None
    }

    users[username] = new_user_data
    save_users(users)

    # Return user without password
    safe_user_data = {k: v for k, v in new_user_data.items() if k != "password"}
    return User(**safe_user_data)

def get_user_by_username(username: str) -> Optional[User]:
    """ Get user by username """
    users = load_users()
    user_data = users.get(username)
    if not user_data:
        return None

    # Return user without password
    safe_user_data = {k: v for k, v in user_data.items() if k != "password"}
    return User(**safe_user_data)

def update_user_login(username: str):
    """ Update user last login timestamp """
    users= load_users()
    if username in users:
        users[username]["last_login"] = datetime.utcnow().isoformat()
        save_users(users)

def validate_token(token: str) -> User:
    """ Validate JWT token """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Get full user info from storage
        user = get_user_by_username(username)
        if not user or not user.active:
            raise HTTPException(status_code=401, detail="User not found or inactive")

        return user
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail= "Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> User:
    """ Get the current user from the token """
    return validate_token(credentials.credentials)

async def get_mock_user() -> User:
    """ Return a mock user for testing - no authentication required """
    return User(username="test_user")

def get_all_users() -> list[User]:
    """Get all users (without passwords) for admin purposes"""
    users = load_users()
    user_list = []
    
    for user_data in users.values():
        safe_user_data = {k: v for k, v in user_data.items() if k != "password"}
        user_list.append(User(**safe_user_data))
    
    return user_list

def user_exists(username: str) -> bool:
    """Check if a user exists"""
    users = load_users()
    return username in users

def get_users_count() -> int:
    """Get total number of users"""
    users = load_users()
    return len(users)