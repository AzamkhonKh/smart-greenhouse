"""
Smart Greenhouse IoT System - Authentication Router
User authentication, registration, and session management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import logging

from database import get_async_db
from auth import AuthService, get_current_user, UserRole
from schemas import (
    UserLogin, UserCreate, UserUpdate, UserResponse, 
    TokenResponse, APIResponse, ErrorDetail
)
from models import User
from redis_utils import redis_manager
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
    responses={
        401: {"description": "Authentication failed"},
        422: {"description": "Validation error"}
    }
)

@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User Login",
    description="Authenticate user with username/password and return JWT token"
)
async def login(
    user_data: UserLogin,
    db: Session = Depends(get_async_db)
):
    """Authenticate user and return access token"""
    try:
        # Authenticate user
        user = await AuthService.authenticate_user(
            user_data.username, 
            user_data.password, 
            db
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "authentication_failed",
                    "message": "Invalid username or password"
                }
            )
        
        # Create access token
        token_data = {
            "sub": user.username,
            "user_id": user.user_id,
            "role": user.role.value
        }
        
        access_token = AuthService.create_access_token(token_data)
        
        # Store session in Redis
        session_data = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value,
            "login_time": datetime.utcnow().isoformat()
        }
        
        await redis_manager.create_session(access_token, session_data)
        
        # Prepare user response
        user_response = UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "login_failed",
                "message": "Login process failed"
            }
        )

@router.post(
    "/register",
    response_model=APIResponse,
    summary="User Registration",
    description="Register new user (admin only)",
    dependencies=[Depends(get_current_user)]
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new user (admin only)"""
    try:
        # Check if current user is admin
        if current_user.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_permissions",
                    "message": "Only administrators can register new users"
                }
            )
        
        # Check if username already exists
        existing_user = db.query(User).filter(User.username == user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "username_exists",
                    "message": "Username already exists"
                }
            )
        
        # Check if email already exists
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "email_exists",
                    "message": "Email already registered"
                }
            )
        
        # Create new user
        hashed_password = AuthService.hash_password(user_data.password)
        
        new_user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log user creation
        logger.info(f"User created: {new_user.username} by {current_user.username}")
        
        user_response = UserResponse(
            user_id=new_user.user_id,
            username=new_user.username,
            email=new_user.email,
            full_name=new_user.full_name,
            role=new_user.role,
            is_active=new_user.is_active,
            created_at=new_user.created_at,
            last_login=new_user.last_login
        )
        
        return APIResponse(
            success=True,
            data=user_response,
            message="User registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "registration_failed",
                "message": "User registration failed"
            }
        )

@router.post(
    "/logout",
    response_model=APIResponse,
    summary="User Logout",
    description="Logout user and invalidate session"
)
async def logout(current_user: User = Depends(get_current_user)):
    """Logout user and invalidate session"""
    try:
        # Get token from request (would need to extract from request)
        # For now, we'll invalidate all sessions for this user
        await redis_manager.invalidate_user_sessions(current_user.user_id)
        
        logger.info(f"User logged out: {current_user.username}")
        
        return APIResponse(
            success=True,
            message="Logged out successfully"
        )
        
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "logout_failed",
                "message": "Logout process failed"
            }
        )

@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get current authenticated user information"
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return UserResponse(
        user_id=current_user.user_id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login=current_user.last_login
    )

@router.put(
    "/me",
    response_model=APIResponse,
    summary="Update Current User",
    description="Update current user profile information"
)
async def update_current_user(
    user_update: UserUpdate,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        # Update allowed fields
        if user_update.email is not None:
            # Check if email is already taken by another user
            existing_email = db.query(User).filter(
                User.email == user_update.email,
                User.user_id != current_user.user_id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "email_exists",
                        "message": "Email already registered"
                    }
                )
            current_user.email = user_update.email
        
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        
        # Role and is_active can only be changed by admin
        if user_update.role is not None or user_update.is_active is not None:
            if current_user.role != UserRole.admin:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "error": "insufficient_permissions",
                        "message": "Only administrators can change role or status"
                    }
                )
            
            if user_update.role is not None:
                current_user.role = user_update.role
            if user_update.is_active is not None:
                current_user.is_active = user_update.is_active
        
        current_user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(current_user)
        
        user_response = UserResponse(
            user_id=current_user.user_id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
        
        return APIResponse(
            success=True,
            data=user_response,
            message="Profile updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_failed",
                "message": "Profile update failed"
            }
        )

@router.post(
    "/change-password",
    response_model=APIResponse,
    summary="Change Password",
    description="Change user password"
)
async def change_password(
    current_password: str,
    new_password: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Change user password"""
    try:
        # Verify current password
        if not AuthService.verify_password(current_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_password",
                    "message": "Current password is incorrect"
                }
            )
        
        # Validate new password strength (basic validation)
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "weak_password",
                    "message": "Password must be at least 6 characters long"
                }
            )
        
        # Hash new password
        new_password_hash = AuthService.hash_password(new_password)
        
        # Update password
        current_user.password_hash = new_password_hash
        current_user.updated_at = datetime.utcnow()
        db.commit()
        
        # Invalidate all sessions for security
        await redis_manager.invalidate_user_sessions(current_user.user_id)
        
        logger.info(f"Password changed for user: {current_user.username}")
        
        return APIResponse(
            success=True,
            message="Password changed successfully. Please login again."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "password_change_failed",
                "message": "Password change failed"
            }
        )

@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Token",
    description="Refresh access token using current session"
)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh access token"""
    try:
        # Create new access token
        token_data = {
            "sub": current_user.username,
            "user_id": current_user.user_id,
            "role": current_user.role.value
        }
        
        new_access_token = AuthService.create_access_token(token_data)
        
        # Update session in Redis
        session_data = {
            "user_id": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role.value,
            "refresh_time": datetime.utcnow().isoformat()
        }
        
        await redis_manager.create_session(new_access_token, session_data)
        
        user_response = UserResponse(
            user_id=current_user.user_id,
            username=current_user.username,
            email=current_user.email,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            created_at=current_user.created_at,
            last_login=current_user.last_login
        )
        
        return TokenResponse(
            access_token=new_access_token,
            token_type="bearer",
            expires_in=settings.JWT_EXPIRE_MINUTES * 60,
            user=user_response
        )
        
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "refresh_failed",
                "message": "Token refresh failed"
            }
        )
