"""
Dependency injection helpers for FastAPI
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.database import get_db_session
from app.core.auth import verify_jwt_token, get_current_user
from app.utils.redis_utils import get_redis
from app.core.config import get_settings

# Security
security = HTTPBearer()
settings = get_settings()


async def get_db() -> AsyncSession:
    """Database dependency"""
    async with get_db_session() as session:
        yield session


async def get_redis_client():
    """Redis dependency"""
    return await get_redis()


async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user"""
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        user = await get_current_user(db, payload.get("sub"))
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_admin_user(
    current_user = Depends(get_current_active_user)
):
    """Get current user with admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user
