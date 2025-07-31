"""
API Router for v1 endpoints
"""

from fastapi import APIRouter

from app.api.v1 import (
    auth_router,
    nodes_router,
    sensors_router,
    actuators_router,
    analytics_router,
    users_router,
    zones_router,
    health_router
)

api_router = APIRouter()

# Include all route modules
api_router.include_router(
    auth_router.router,
    prefix="/auth",
    tags=["Authentication"]
)

api_router.include_router(
    nodes_router.router,
    prefix="/nodes",
    tags=["Nodes"]
)

api_router.include_router(
    sensors_router.router,
    prefix="/sensors",
    tags=["Sensors"]
)

api_router.include_router(
    actuators_router.router,
    prefix="/actuators",
    tags=["Actuators"]
)

api_router.include_router(
    analytics_router.router,
    prefix="/analytics",
    tags=["Analytics"]
)

api_router.include_router(
    users_router.router,
    prefix="/users",
    tags=["Users"]
)

api_router.include_router(
    zones_router.router,
    prefix="/zones",
    tags=["Zones"]
)

api_router.include_router(
    health_router.router,
    prefix="/health",
    tags=["Health"]
)
