"""
Custom exception handlers for the application
"""

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import logging

logger = logging.getLogger(__name__)


class GreenhouseException(Exception):
    """Base exception for greenhouse application"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NodeNotFoundException(GreenhouseException):
    """Exception raised when a node is not found"""
    def __init__(self, node_id: str):
        super().__init__(f"Node {node_id} not found", 404)


class SensorNotFoundException(GreenhouseException):
    """Exception raised when a sensor is not found"""
    def __init__(self, sensor_id: str):
        super().__init__(f"Sensor {sensor_id} not found", 404)


class AuthenticationException(GreenhouseException):
    """Exception raised for authentication errors"""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, 401)


class AuthorizationException(GreenhouseException):
    """Exception raised for authorization errors"""
    def __init__(self, message: str = "Not authorized"):
        super().__init__(message, 403)


class ValidationException(GreenhouseException):
    """Exception raised for validation errors"""
    def __init__(self, message: str):
        super().__init__(message, 422)


async def greenhouse_exception_handler(request: Request, exc: GreenhouseException):
    """Handle custom greenhouse exceptions"""
    logger.error(f"Greenhouse exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "status_code": exc.status_code
        }
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """Handle SQLAlchemy database exceptions"""
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "message": "A database error occurred",
            "status_code": 500
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": "An internal server error occurred",
            "status_code": 500
        }
    )
