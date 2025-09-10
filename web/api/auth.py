from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timedelta

from ..middleware.auth import (
    authenticate_user, create_access_token, create_user,
    load_users, save_users, get_user_by_username, update_user_login,
    get_current_user
)

from ..models.user import UserLogin, Token, UserCreate, User
from ..models.common import APIResponse
from ..config import settings

router = APIRouter()

@router.post("/login", response_model=APIResponse[Token])
async def login(user_credentials: UserLogin):
    """Login for existing users"""
    if not authenticate_user(user_credentials.username, user_credentials.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Update last login using the helper function
    update_user_login(user_credentials.username)

    # Create token with extended expiration for internal network
    access_token = create_access_token(
        data={"sub": user_credentials.username},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes)
    )

    return APIResponse(
        status="success",
        data=Token(access_token=access_token, token_type="bearer"),
        message="Login successful"
    )

@router.post("/register", response_model=APIResponse[User])
async def register(new_user: UserCreate):
    """Register a new user"""
    try:
        user = create_user(new_user.username, new_user.email, new_user.password, new_user.role)
        return APIResponse(
            status="success",
            data=user,
            message="User registered successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/me", response_model=APIResponse[User])
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return APIResponse(
        status="success", 
        data=current_user,
        message="User info retrieved"
    )