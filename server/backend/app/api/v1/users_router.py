"""
Smart Greenhouse IoT System - Users Router
User management endpoints for administrators
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from typing import List, Optional
import logging

from database import get_async_db
from auth import get_current_user, require_role, UserRole
from schemas import (
    UserCreate, UserUpdate, UserResponse, APIResponse, 
    PaginationParams, PaginatedResponse
)
from models import User
from redis_utils import redis_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/users",
    tags=["User Management"],
    dependencies=[Depends(require_role(UserRole.admin))],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin role required"},
        404: {"description": "User not found"}
    }
)

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List Users",
    description="Get paginated list of all users (admin only)"
)
async def list_users(
    pagination: PaginationParams = Depends(),
    role: Optional[UserRole] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search in username, email, or full name"),
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of users with filtering"""
    try:
        query = db.query(User)
        
        # Apply filters
        filters = []
        if role:
            filters.append(User.role == role)
        if is_active is not None:
            filters.append(User.is_active == is_active)
        if search:
            search_filter = or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        offset = (pagination.page - 1) * pagination.size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(pagination.size).all()
        
        # Convert to response format
        user_responses = []
        for user in users:
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
            user_responses.append(user_response)
        
        return PaginatedResponse.create(
            items=user_responses,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
    except Exception as e:
        logger.error(f"List users failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "list_users_failed",
                "message": "Failed to retrieve users"
            }
        )

@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User",
    description="Get detailed information about a specific user"
)
async def get_user(
    user_id: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed user information"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        return UserResponse(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login=user.last_login
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_user_failed",
                "message": "Failed to retrieve user"
            }
        )

@router.put(
    "/{user_id}",
    response_model=APIResponse,
    summary="Update User",
    description="Update user information (admin only)"
)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Update user information"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        # Prevent admin from deactivating themselves
        if user_id == current_user.user_id and user_update.is_active is False:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "cannot_deactivate_self",
                    "message": "Cannot deactivate your own account"
                }
            )
        
        # Check if email is already taken by another user
        if user_update.email is not None and user_update.email != user.email:
            existing_email = db.query(User).filter(
                User.email == user_update.email,
                User.user_id != user_id
            ).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "email_exists",
                        "message": "Email already registered to another user"
                    }
                )
        
        # Update fields
        if user_update.email is not None:
            user.email = user_update.email
        if user_update.full_name is not None:
            user.full_name = user_update.full_name
        if user_update.role is not None:
            user.role = user_update.role
        if user_update.is_active is not None:
            user.is_active = user_update.is_active
            
            # If deactivating user, invalidate their sessions
            if not user_update.is_active:
                await redis_manager.invalidate_user_sessions(user_id)
        
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        logger.info(f"User updated: {user_id} by {current_user.username}")
        
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
        
        return APIResponse(
            success=True,
            data=user_response,
            message="User updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update user failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_user_failed",
                "message": "Failed to update user"
            }
        )

@router.delete(
    "/{user_id}",
    response_model=APIResponse,
    summary="Delete User",
    description="Delete a user account (admin only)"
)
async def delete_user(
    user_id: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Delete user account"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        # Prevent admin from deleting themselves
        if user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "cannot_delete_self",
                    "message": "Cannot delete your own account"
                }
            )
        
        # Check if this is the last admin
        if user.role == UserRole.admin:
            admin_count = db.query(User).filter(
                User.role == UserRole.admin,
                User.is_active == True
            ).count()
            if admin_count <= 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "cannot_delete_last_admin",
                        "message": "Cannot delete the last active administrator"
                    }
                )
        
        # Invalidate user sessions
        await redis_manager.invalidate_user_sessions(user_id)
        
        # Delete user
        db.delete(user)
        db.commit()
        
        logger.info(f"User deleted: {user_id} by {current_user.username}")
        
        return APIResponse(
            success=True,
            message="User deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete user failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "delete_user_failed",
                "message": "Failed to delete user"
            }
        )

@router.post(
    "/{user_id}/reset-password",
    response_model=APIResponse,
    summary="Reset User Password",
    description="Reset a user's password (admin only)"
)
async def reset_user_password(
    user_id: str,
    new_password: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Reset user password"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        # Validate new password strength
        if len(new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "weak_password",
                    "message": "Password must be at least 6 characters long"
                }
            )
        
        # Hash new password
        from auth import AuthService
        new_password_hash = AuthService.hash_password(new_password)
        
        # Update password
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Invalidate all sessions for security
        await redis_manager.invalidate_user_sessions(user_id)
        
        logger.info(f"Password reset for user: {user_id} by {current_user.username}")
        
        return APIResponse(
            success=True,
            message="Password reset successfully. User will need to login again."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Reset password failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "reset_password_failed",
                "message": "Failed to reset password"
            }
        )

@router.post(
    "/{user_id}/activate",
    response_model=APIResponse,
    summary="Activate User",
    description="Activate a deactivated user account"
)
async def activate_user(
    user_id: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Activate user account"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        if user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "user_already_active",
                    "message": "User is already active"
                }
            )
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"User activated: {user_id} by {current_user.username}")
        
        return APIResponse(
            success=True,
            message="User activated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Activate user failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "activate_user_failed",
                "message": "Failed to activate user"
            }
        )

@router.post(
    "/{user_id}/deactivate",
    response_model=APIResponse,
    summary="Deactivate User",
    description="Deactivate a user account"
)
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Deactivate user account"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        # Prevent admin from deactivating themselves
        if user_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "cannot_deactivate_self",
                    "message": "Cannot deactivate your own account"
                }
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "user_already_inactive",
                    "message": "User is already inactive"
                }
            )
        
        user.is_active = False
        user.updated_at = datetime.utcnow()
        db.commit()
        
        # Invalidate user sessions
        await redis_manager.invalidate_user_sessions(user_id)
        
        logger.info(f"User deactivated: {user_id} by {current_user.username}")
        
        return APIResponse(
            success=True,
            message="User deactivated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deactivate user failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "deactivate_user_failed",
                "message": "Failed to deactivate user"
            }
        )

@router.get(
    "/{user_id}/sessions",
    response_model=List[dict],
    summary="Get User Sessions",
    description="Get active sessions for a user"
)
async def get_user_sessions(
    user_id: str,
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get active sessions for user"""
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "user_not_found",
                    "message": f"User {user_id} not found"
                }
            )
        
        # Get sessions from Redis
        sessions = await redis_manager.get_user_sessions(user_id)
        
        return sessions
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user sessions failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_sessions_failed",
                "message": "Failed to retrieve user sessions"
            }
        )
