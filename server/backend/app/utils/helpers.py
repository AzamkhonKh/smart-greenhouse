"""
Common utility functions
"""

import hashlib
import secrets
import string
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import json


def generate_api_key(prefix: str = "gh", length: int = 32) -> str:
    """Generate a secure API key"""
    random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(length))
    return f"{prefix}_{random_part}"


def hash_password(password: str) -> str:
    """Hash a password using SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash"""
    return hash_password(password) == hashed


def utc_now() -> datetime:
    """Get current UTC datetime"""
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%dT%H:%M:%S.%fZ") -> str:
    """Format datetime to string"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime(format_str)


def parse_datetime(dt_str: str) -> datetime:
    """Parse datetime string to datetime object"""
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback to basic format
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%S")


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    return filename


def calculate_battery_level(voltage: float, min_voltage: float = 3.0, max_voltage: float = 4.2) -> float:
    """Calculate battery percentage from voltage"""
    if voltage <= min_voltage:
        return 0.0
    if voltage >= max_voltage:
        return 100.0
    return ((voltage - min_voltage) / (max_voltage - min_voltage)) * 100


def validate_node_id(node_id: str) -> bool:
    """Validate node ID format"""
    if not node_id or len(node_id) < 3:
        return False
    # Node ID should contain only alphanumeric characters and underscores
    return all(c.isalnum() or c == '_' for c in node_id)


def validate_zone_id(zone_id: str) -> bool:
    """Validate zone ID format (e.g., A1, B2, C3)"""
    if not zone_id or len(zone_id) != 2:
        return False
    return zone_id[0].isalpha() and zone_id[1].isdigit()


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def serialize_datetime(obj: Any) -> str:
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return format_datetime(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """Safely load JSON string with fallback"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to max length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def bytes_to_human_readable(bytes_count: int) -> str:
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_count < 1024.0:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024.0
    return f"{bytes_count:.1f} PB"
