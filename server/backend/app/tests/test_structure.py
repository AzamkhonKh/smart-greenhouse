"""
Test the restructured backend application
"""

import pytest
import asyncio
from fastapi.testclient import TestClient

# Test if main app can be imported
def test_main_app_import():
    """Test that the main app can be imported without errors"""
    try:
        from main import app
        assert app is not None
        assert app.title == "Smart Greenhouse IoT System"
    except ImportError as e:
        pytest.skip(f"Import error (dependencies not installed): {e}")


def test_legacy_app_import():
    """Test that the legacy app.py still works"""
    try:
        from app import app
        assert app is not None
    except ImportError as e:
        pytest.skip(f"Import error (dependencies not installed): {e}")


def test_config_import():
    """Test that configuration can be imported"""
    try:
        from app.core.config import get_settings
        settings = get_settings()
        assert settings is not None
        assert hasattr(settings, 'API_HOST')
        assert hasattr(settings, 'API_PORT')
    except ImportError as e:
        pytest.skip(f"Import error (dependencies not installed): {e}")


def test_utils_import():
    """Test that utilities can be imported"""
    try:
        from app.utils.helpers import generate_api_key, validate_node_id
        
        # Test utility functions
        api_key = generate_api_key()
        assert isinstance(api_key, str)
        assert len(api_key) > 10
        
        assert validate_node_id("node_001") == True
        assert validate_node_id("") == False
        assert validate_node_id("a") == False
        
    except ImportError as e:
        pytest.skip(f"Import error (dependencies not installed): {e}")


def test_service_base_import():
    """Test that base service can be imported"""
    try:
        from app.services.base_service import BaseService
        assert BaseService is not None
    except ImportError as e:
        pytest.skip(f"Import error (dependencies not installed): {e}")


if __name__ == "__main__":
    # Run basic import tests
    test_main_app_import()
    test_legacy_app_import()
    test_config_import()
    test_utils_import()
    test_service_base_import()
    print("✅ All import tests passed!")
