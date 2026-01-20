"""Authentication routes."""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm

from app.auth import authenticate_user, create_access_token, get_current_user
from app.config import get_settings
from app.database import get_db
from app.limiter import limiter
from app.schemas import LoginRequest, Token
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """Login and get access token."""
    if not await authenticate_user(db, form_data.username, form_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.post("/login/json", response_model=Token)
@limiter.limit("5/minute")
async def login_json(
    request: Request,
    login_request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
) -> Token:
    """Login with JSON body and get access token."""
    if not await authenticate_user(db, login_request.username, login_request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": login_request.username},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
async def get_me(
    current_user: Annotated[str, Depends(get_current_user)]
) -> dict:
    """Get current user information."""
    return {"username": current_user}


@router.post("/verify")
async def verify_token(
    current_user: Annotated[str, Depends(get_current_user)]
) -> dict:
    """Verify if the current token is valid."""
    return {"valid": True, "username": current_user}


from pydantic import BaseModel

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

@router.put("/password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[str, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Change user password."""
    # Verify current password
    if not await authenticate_user(db, current_user, password_data.current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    from app.auth import get_password_hash
    from app.models import User
    from sqlalchemy import select
    
    result = await db.execute(select(User).where(User.username == current_user))
    user = result.scalar_one()
    
    user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password updated successfully"}
