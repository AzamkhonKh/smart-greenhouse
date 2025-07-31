"""
Base service class for the application
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BaseService(ABC):
    """Base service class with common functionality"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass
    
    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for the service"""
        return {
            "service": self.__class__.__name__,
            "status": "healthy"
        }
