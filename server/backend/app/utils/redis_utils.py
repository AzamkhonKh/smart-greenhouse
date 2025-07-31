"""
Smart Greenhouse IoT System - Redis Utilities
High-performance caching and session management
"""

import redis.asyncio as redis
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import hashlib

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class RedisManager:
    """Redis connection and operations manager"""
    
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self._connection_pool = None
    
    async def connect(self):
        """Initialize Redis connection"""
        try:
            self._connection_pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                decode_responses=True
            )
            self.redis = redis.Redis(connection_pool=self._connection_pool)
            
            # Test connection
            await self.redis.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            raise
    
    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    async def ping(self) -> bool:
        """Test Redis connectivity"""
        try:
            if not self.redis:
                await self.connect()
            await self.redis.ping()
            return True
        except Exception as e:
            logger.error(f"Redis ping failed: {str(e)}")
            return False
    
    # API Key Management
    async def cache_api_key(self, api_key: str, node_id: str, ttl: int = None) -> bool:
        """Cache API key for fast lookup"""
        try:
            key = f"api_key:{api_key}"
            ttl = ttl or settings.API_KEY_CACHE_TTL
            await self.redis.setex(key, ttl, node_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cache API key: {str(e)}")
            return False
    
    async def get_node_by_api_key(self, api_key: str) -> Optional[str]:
        """Get node ID by API key from cache"""
        try:
            key = f"api_key:{api_key}"
            node_id = await self.redis.get(key)
            return node_id
        except Exception as e:
            logger.error(f"Failed to get node by API key: {str(e)}")
            return None
    
    async def invalidate_api_key(self, api_key: str) -> bool:
        """Remove API key from cache"""
        try:
            key = f"api_key:{api_key}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to invalidate API key: {str(e)}")
            return False
    
    # Session Management
    async def create_session(self, session_token: str, user_data: Dict[str, Any], ttl: int = None) -> bool:
        """Create user session"""
        try:
            key = f"session:{session_token}"
            ttl = ttl or settings.SESSION_TTL
            data = json.dumps(user_data, default=str)
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to create session: {str(e)}")
            return False
    
    async def get_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get session data"""
        try:
            key = f"session:{session_token}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get session: {str(e)}")
            return None
    
    async def update_session(self, session_token: str, user_data: Dict[str, Any], extend_ttl: bool = True) -> bool:
        """Update session data"""
        try:
            key = f"session:{session_token}"
            data = json.dumps(user_data, default=str)
            
            if extend_ttl:
                await self.redis.setex(key, settings.SESSION_TTL, data)
            else:
                await self.redis.set(key, data, keepttl=True)
            return True
        except Exception as e:
            logger.error(f"Failed to update session: {str(e)}")
            return False
    
    async def delete_session(self, session_token: str) -> bool:
        """Delete user session"""
        try:
            key = f"session:{session_token}"
            await self.redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Failed to delete session: {str(e)}")
            return False
    
    # Rate Limiting
    async def check_rate_limit(self, identifier: str, limit: int, window_seconds: int = 60) -> Dict[str, Any]:
        """Check and update rate limit using sliding window"""
        try:
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            key = f"rate_limit:{identifier}"
            
            # Use Redis sorted set for sliding window
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(key, 0, window_start.timestamp())
            
            # Add current request
            pipe.zadd(key, {str(now.timestamp()): now.timestamp()})
            
            # Count requests in window
            pipe.zcard(key)
            
            # Set expiration
            pipe.expire(key, window_seconds * 2)
            
            results = await pipe.execute()
            current_count = results[2]  # zcard result
            
            is_allowed = current_count <= limit
            remaining = max(0, limit - current_count)
            
            # Get reset time (when oldest request will expire)
            oldest_requests = await self.redis.zrange(key, 0, 0, withscores=True)
            reset_time = None
            if oldest_requests:
                reset_time = datetime.fromtimestamp(oldest_requests[0][1]) + timedelta(seconds=window_seconds)
            
            return {
                "allowed": is_allowed,
                "limit": limit,
                "current": current_count,
                "remaining": remaining,
                "reset_time": reset_time.isoformat() + "Z" if reset_time else None
            }
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {str(e)}")
            # Allow request on Redis failure
            return {
                "allowed": True,
                "limit": limit,
                "current": 0,
                "remaining": limit,
                "reset_time": None,
                "error": str(e)
            }
    
    # Node Heartbeat
    async def update_node_heartbeat(self, node_id: str, status_data: Dict[str, Any], ttl: int = 300) -> bool:
        """Update node heartbeat status"""
        try:
            key = f"heartbeat:{node_id}"
            data = json.dumps({
                **status_data,
                "last_update": datetime.utcnow().isoformat() + "Z"
            }, default=str)
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to update node heartbeat: {str(e)}")
            return False
    
    async def get_node_heartbeat(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node heartbeat status"""
        try:
            key = f"heartbeat:{node_id}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get node heartbeat: {str(e)}")
            return None
    
    async def get_all_node_heartbeats(self) -> Dict[str, Dict[str, Any]]:
        """Get all node heartbeat statuses"""
        try:
            pattern = "heartbeat:*"
            keys = await self.redis.keys(pattern)
            
            if not keys:
                return {}
            
            # Use pipeline for efficient bulk retrieval
            pipe = self.redis.pipeline()
            for key in keys:
                pipe.get(key)
            
            results = await pipe.execute()
            
            heartbeats = {}
            for key, data in zip(keys, results):
                if data:
                    node_id = key.split(":", 1)[1]
                    heartbeats[node_id] = json.loads(data)
            
            return heartbeats
            
        except Exception as e:
            logger.error(f"Failed to get all node heartbeats: {str(e)}")
            return {}
    
    # Sensor Data Cache
    async def cache_latest_sensor_data(self, node_id: str, sensor_data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Cache latest sensor readings for quick access"""
        try:
            key = f"sensor_data:{node_id}"
            data = json.dumps({
                **sensor_data,
                "cached_at": datetime.utcnow().isoformat() + "Z"
            }, default=str)
            await self.redis.setex(key, ttl, data)
            return True
        except Exception as e:
            logger.error(f"Failed to cache sensor data: {str(e)}")
            return False
    
    async def get_latest_sensor_data(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get cached latest sensor readings"""
        try:
            key = f"sensor_data:{node_id}"
            data = await self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.error(f"Failed to get cached sensor data: {str(e)}")
            return None
    
    # API Statistics
    async def increment_api_stat(self, node_id: str, endpoint: str, date: str = None) -> bool:
        """Increment API usage statistics"""
        try:
            if not date:
                date = datetime.utcnow().strftime("%Y-%m-%d")
            
            key = f"api_stats:{node_id}:{endpoint}:{date}"
            await self.redis.incr(key)
            await self.redis.expire(key, 86400 * 7)  # Keep for 7 days
            return True
        except Exception as e:
            logger.error(f"Failed to increment API stat: {str(e)}")
            return False
    
    async def get_api_stats(self, node_id: str, days: int = 7) -> Dict[str, Dict[str, int]]:
        """Get API usage statistics for a node"""
        try:
            stats = {}
            for i in range(days):
                date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
                pattern = f"api_stats:{node_id}:*:{date}"
                keys = await self.redis.keys(pattern)
                
                daily_stats = {}
                if keys:
                    pipe = self.redis.pipeline()
                    for key in keys:
                        pipe.get(key)
                    
                    results = await pipe.execute()
                    
                    for key, count in zip(keys, results):
                        parts = key.split(":")
                        endpoint = parts[2]
                        daily_stats[endpoint] = int(count) if count else 0
                
                stats[date] = daily_stats
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get API stats: {str(e)}")
            return {}
    
    # General utilities
    async def health_check(self) -> Dict[str, Any]:
        """Redis health check"""
        try:
            start_time = datetime.utcnow()
            await self.redis.ping()
            response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            info = await self.redis.info()
            
            return {
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "connected_clients": info.get("connected_clients", 0),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "redis_version": info.get("redis_version", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Redis health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

# Global Redis manager instance
redis_manager = RedisManager()


async def init_redis():
    """Initialize Redis connection"""
    try:
        await redis_manager.connect()
        logger.info("✅ Redis initialized successfully")
    except Exception as e:
        logger.error(f"❌ Redis initialization failed: {e}")
        raise


async def close_redis():
    """Close Redis connection"""
    try:
        await redis_manager.disconnect()
        logger.info("✅ Redis connection closed successfully")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")


async def get_redis():
    """Get Redis client for dependency injection"""
    if not redis_manager.redis:
        await redis_manager.connect()
    return redis_manager.redis


async def test_redis_connection():
    """Test Redis connection"""
    try:
        await redis_manager.connect()
        result = await redis_manager.ping()
        if result:
            logger.info("Redis connection test passed")
            return True
        else:
            raise Exception("Redis ping failed")
    except Exception as e:
        logger.error(f"Redis connection test failed: {e}")
        raise
