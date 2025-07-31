"""
Smart Greenhouse IoT System - Authentication & Authorization
JWT-based user authentication and API key authentication for nodes
"""

import jwt
from jwt.exceptions import PyJWTError
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import logging

from config import settings, NODE_API_KEYS
from database import get_db
from models import User, Node, UserRole

logger = logging.getLogger(__name__)

# Import redis_manager after other imports to avoid circular imports
try:
    from redis_utils import redis_manager
except ImportError:
    logger.warning("Redis utilities not available, session management disabled")
    redis_manager = None

# Security schemes
security = HTTPBearer()
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

class AuthService:
    """Authentication service for users and API keys"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "token_expired",
                    "message": "Token has expired"
                }
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Could not validate credentials"
                }
            )
    
    @staticmethod
    async def authenticate_user(username: str, password: str, db: Session) -> Optional[User]:
        """Authenticate user with username/password"""
        try:
            user = db.query(User).filter(User.username == username, User.is_active == True).first()
            if not user:
                return None
            
            if not AuthService.verify_password(password, user.password_hash):
                return None
            
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
            return user
            
        except Exception as e:
            logger.error(f"User authentication failed: {str(e)}")
            return None
    
    @staticmethod
    async def authenticate_api_key(api_key: str) -> Optional[str]:
        """Authenticate node using API key"""
        try:
            # First check Redis cache if available
            if redis_manager:
                node_id = await redis_manager.get_node_by_api_key(api_key)
                if node_id:
                    return node_id
            
            # Check static API keys (fallback)
            if api_key in NODE_API_KEYS:
                node_id = NODE_API_KEYS[api_key]
                # Cache the result if Redis is available
                if redis_manager:
                    await redis_manager.cache_api_key(api_key, node_id)
                return node_id
            
            return None
            
        except Exception as e:
            logger.error(f"API key authentication failed: {str(e)}")
            return None
    
    @staticmethod
    def authenticate_api_key_sync(api_key: str) -> Optional[str]:
        """Synchronous version of API key authentication for CoAP server"""
        try:
            # Check static API keys (synchronous fallback)
            if api_key in NODE_API_KEYS:
                node_id = NODE_API_KEYS[api_key]
                return node_id
            
            return None
            
        except Exception as e:
            logger.error(f"Sync API key authentication failed: {str(e)}")
            return None

# Dependency functions
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token"""
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Check Redis session first if available
        if redis_manager:
            session_data = await redis_manager.get_session(token)
            if session_data:
                user_id = session_data.get("user_id")
                if user_id:
                    query = select(User).where(User.user_id == user_id, User.is_active == True)
                    result = await db.execute(query)
                    user = result.scalar_one_or_none()
                    if user:
                        # Extend session
                        await redis_manager.update_session(token, session_data)
                        return user
        
        # Verify JWT token
        payload = AuthService.verify_token(token)
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "invalid_token",
                    "message": "Token payload invalid"
                }
            )
        
        # Get user from database
        user = db.query(User).filter(User.user_id == user_id, User.is_active == True).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": "user_not_found",
                    "message": "User not found or inactive"
                }
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "authentication_failed",
                "message": "Could not validate credentials"
            }
        )

async def get_current_node(api_key: str = Security(api_key_header)) -> str:
    """Get current authenticated node from API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": "API key required in X-API-Key header"
            }
        )
    
    node_id = await AuthService.authenticate_api_key(api_key)
    if not node_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key"
            }
        )
    
    return node_id

async def get_current_node_object(
    api_key: str = Security(api_key_header),
    db: AsyncSession = Depends(get_db)
) -> Node:
    """Get current authenticated node object from API key"""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "missing_api_key",
                "message": "API key required in X-API-Key header"
            }
        )
    
    node_id = await AuthService.authenticate_api_key(api_key)
    if not node_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "invalid_api_key",
                "message": "Invalid API key"
            }
        )
    
    # Get the actual node object from database using async syntax
    query = select(Node).where(Node.node_id == node_id)
    result = await db.execute(query)
    node = result.scalar_one_or_none()
    
    if not node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "node_not_found",
                "message": f"Node {node_id} not found in database"
            }
        )
    
    return node

# Authorization decorators
def require_role(required_role: UserRole):
    """Decorator to require specific user role"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_hierarchy = {
            UserRole.viewer: 1,
            UserRole.operator: 2,
            UserRole.manager: 3,
            UserRole.admin: 4
        }
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "insufficient_permissions",
                    "message": f"Role '{required_role.value}' or higher required"
                }
            )
        
        return current_user
    
    return role_checker

def require_api_key(current_node: str = Depends(get_current_node)) -> str:
    """Decorator to require valid API key"""
    return current_node

def require_node_object(current_node: Node = Depends(get_current_node_object)) -> Node:
    """Decorator to require valid API key and return Node object"""
    return current_node

# Permission checking functions
async def check_resource_permission(
    user: User,
    resource_type: str,
    resource_id: str,
    action: str,
    db: Session
) -> bool:
    """Check if user has permission for specific resource action"""
    try:
        # Admin has all permissions
        if user.role == UserRole.admin:
            return True
        
        # Check specific permissions
        from models import Permission
        permission = db.query(Permission).filter(
            Permission.user_id == user.user_id,
            Permission.resource_type == resource_type,
            Permission.resource_id == resource_id
        ).first()
        
        if permission:
            # Check if permission is expired
            if permission.expires_at and permission.expires_at < datetime.utcnow():
                return False
            
            # Check if action is allowed
            return action in permission.actions
        
        # Check default role permissions
        default_permissions = get_default_role_permissions(user.role)
        resource_perms = default_permissions.get(resource_type, {})
        return action in resource_perms.get("actions", [])
        
    except Exception as e:
        logger.error(f"Permission check failed: {str(e)}")
        return False

def get_default_role_permissions(role: UserRole) -> Dict[str, Dict[str, Any]]:
    """Get default permissions for user role"""
    permissions = {
        UserRole.viewer: {
            "nodes": {"actions": ["read"]},
            "sensors": {"actions": ["read"]},
            "actuators": {"actions": ["read"]},
            "zones": {"actions": ["read"]},
            "analytics": {"actions": ["read"]}
        },
        UserRole.operator: {
            "nodes": {"actions": ["read"]},
            "sensors": {"actions": ["read", "write"]},
            "actuators": {"actions": ["read", "control"]},
            "zones": {"actions": ["read", "update"]},
            "analytics": {"actions": ["read"]}
        },
        UserRole.manager: {
            "nodes": {"actions": ["read", "update"]},
            "sensors": {"actions": ["read", "write", "configure"]},
            "actuators": {"actions": ["read", "control", "configure"]},
            "zones": {"actions": ["read", "write", "update", "delete"]},
            "analytics": {"actions": ["read"]},
            "users": {"actions": ["read"]}
        },
        UserRole.admin: {
            "*": {"actions": ["*"]}  # Full access to everything
        }
    }
    
    return permissions.get(role, {})

# Synchronous wrapper functions for CoAP server
def verify_api_key_sync(api_key: str) -> Optional[str]:
    """Synchronous API key verification for CoAP server"""
    return AuthService.authenticate_api_key_sync(api_key)
