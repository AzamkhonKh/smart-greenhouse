"""
Smart Greenhouse IoT System - Routers Package
Exports all API routers for the FastAPI application
"""

from .auth_router import router as auth_router
from .nodes_router import router as nodes_router
from .sensors_router import router as sensors_router
from .actuators_router import router as actuators_router
from .zones_router import router as zones_router
from .users_router import router as users_router
from .health_router import router as health_router
from .analytics_router import router as analytics_router

__all__ = [
    "auth_router",
    "nodes_router", 
    "sensors_router",
    "actuators_router",
    "zones_router",
    "users_router",
    "health_router",
    "analytics_router"
]