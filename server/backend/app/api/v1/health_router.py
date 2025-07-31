"""
Smart Greenhouse IoT System - Health Check Router
System health monitoring and status endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from database import get_async_db, engine
from auth import get_current_user
from redis_utils import redis_manager
from schemas import SystemHealthResponse, APIResponse
from models import Node, Sensor, Actuator, SensorReading, NodeStatus, User

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health & Monitoring"],
    responses={
        500: {"description": "Internal server error"},
        503: {"description": "Service unavailable"}
    }
)

@router.get(
    "/",
    response_model=APIResponse,
    summary="Basic Health Check",
    description="Basic API health check endpoint"
)
async def health_check():
    """Basic health check - returns API status"""
    return APIResponse(
        success=True,
        data={
            "status": "healthy",
            "service": "Smart Greenhouse IoT API",
            "version": "1.0.0",
            "timestamp": datetime.utcnow()
        },
        message="API is running normally"
    )

@router.get(
    "/detailed",
    response_model=APIResponse,
    summary="Detailed Health Check",
    description="Comprehensive system health check including database and Redis"
)
async def detailed_health_check(db: Session = Depends(get_async_db)):
    """Detailed health check with database and Redis connectivity"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "services": {}
    }
    
    issues = []
    
    try:
        # Check database connectivity
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = {
            "status": "healthy",
            "response_time_ms": 0  # Would measure actual response time
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_status["services"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        issues.append("database_connection")
    
    try:
        # Check Redis connectivity
        await redis_manager.ping()
        health_status["services"]["redis"] = {
            "status": "healthy",
            "response_time_ms": 0
        }
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        health_status["services"]["redis"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        issues.append("redis_connection")
    
    # Set overall status
    if issues:
        health_status["status"] = "degraded" if len(issues) == 1 else "unhealthy"
        health_status["issues"] = issues
    
    # Return appropriate status code
    status_code = status.HTTP_200_OK
    if health_status["status"] == "unhealthy":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif health_status["status"] == "degraded":
        status_code = status.HTTP_200_OK  # Still operational
    
    return APIResponse(
        success=health_status["status"] != "unhealthy",
        data=health_status,
        message=f"System status: {health_status['status']}"
    )

@router.get(
    "/system",
    response_model=SystemHealthResponse,
    summary="System Overview",
    description="Complete system health overview with node and sensor statistics"
)
async def system_health_overview(db: Session = Depends(get_async_db)):
    """Get comprehensive system health overview"""
    try:
        current_time = datetime.utcnow()
        day_ago = current_time - timedelta(days=1)
        
        # Node statistics
        total_nodes = db.query(Node).count()
        active_nodes = db.query(Node).filter(Node.status == NodeStatus.active).count()
        inactive_nodes = db.query(Node).filter(Node.status == NodeStatus.inactive).count()
        error_nodes = db.query(Node).filter(Node.status == NodeStatus.error).count()
        
        # Sensor statistics
        total_sensors = db.query(Sensor).count()
        active_sensors = db.query(Sensor).filter(Sensor.is_active == True).count()
        
        # Calculate sensor uptime (sensors that have reported in last 24h)
        recent_readings = db.query(SensorReading.sensor_id).filter(
            SensorReading.timestamp >= day_ago
        ).distinct().count()
        
        sensor_uptime_percentage = (recent_readings / total_sensors * 100) if total_sensors > 0 else 0
        
        # Data points in last 24 hours
        data_points_24h = db.query(SensorReading).filter(
            SensorReading.timestamp >= day_ago
        ).count()
        
        # System status determination
        system_status = "healthy"
        if active_nodes < total_nodes * 0.8:  # Less than 80% nodes active
            system_status = "degraded"
        if active_nodes < total_nodes * 0.5:  # Less than 50% nodes active
            system_status = "critical"
        if sensor_uptime_percentage < 70:  # Less than 70% sensor uptime
            system_status = "degraded"
        
        return SystemHealthResponse(
            timestamp=current_time,
            total_nodes=total_nodes,
            active_nodes=active_nodes,
            inactive_nodes=inactive_nodes,
            error_nodes=error_nodes,
            total_sensors=total_sensors,
            active_sensors=active_sensors,
            sensor_uptime_percentage=round(sensor_uptime_percentage, 2),
            data_points_24h=data_points_24h,
            alerts_count=0,  # Would get from alerts table
            system_status=system_status
        )
        
    except Exception as e:
        logger.error(f"System health overview failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "health_check_failed",
                "message": "Failed to retrieve system health overview"
            }
        )

@router.get(
    "/metrics",
    response_model=APIResponse,
    summary="System Metrics",
    description="Detailed system performance metrics"
)
async def system_metrics(db: Session = Depends(get_async_db)):
    """Get detailed system performance metrics"""
    try:
        current_time = datetime.utcnow()
        hour_ago = current_time - timedelta(hours=1)
        day_ago = current_time - timedelta(days=1)
        
        # Database metrics
        db_metrics = {}
        try:
            # Get database size (PostgreSQL specific)
            result = db.execute(text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as db_size,
                    (SELECT count(*) FROM sensor_readings WHERE timestamp >= :hour_ago) as readings_last_hour,
                    (SELECT count(*) FROM actuator_commands WHERE timestamp >= :hour_ago) as commands_last_hour
            """), {"hour_ago": hour_ago})
            
            row = result.fetchone()
            if row:
                db_metrics = {
                    "database_size": row[0],
                    "readings_last_hour": row[1],
                    "commands_last_hour": row[2]
                }
        except Exception as e:
            logger.warning(f"Could not get database metrics: {str(e)}")
            db_metrics = {"error": "metrics_unavailable"}
        
        # Redis metrics
        redis_metrics = {}
        try:
            redis_info = await redis_manager.get_info()
            redis_metrics = {
                "connected_clients": redis_info.get("connected_clients", 0),
                "used_memory_human": redis_info.get("used_memory_human", "0B"),
                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                "keyspace_misses": redis_info.get("keyspace_misses", 0)
            }
        except Exception as e:
            logger.warning(f"Could not get Redis metrics: {str(e)}")
            redis_metrics = {"error": "metrics_unavailable"}
        
        # Node communication metrics
        node_metrics = {}
        try:
            # Get node communication statistics
            result = db.execute(text("""
                SELECT 
                    COUNT(*) as total_nodes,
                    COUNT(CASE WHEN last_seen >= :hour_ago THEN 1 END) as active_last_hour,
                    COUNT(CASE WHEN last_seen >= :day_ago THEN 1 END) as active_last_day,
                    AVG(EXTRACT(EPOCH FROM (NOW() - last_seen))/60) as avg_minutes_since_contact
                FROM nodes
                WHERE last_seen IS NOT NULL
            """), {"hour_ago": hour_ago, "day_ago": day_ago})
            
            row = result.fetchone()
            if row:
                node_metrics = {
                    "total_nodes": row[0],
                    "active_last_hour": row[1],
                    "active_last_day": row[2],
                    "avg_minutes_since_contact": round(row[3] or 0, 2)
                }
        except Exception as e:
            logger.warning(f"Could not get node metrics: {str(e)}")
            node_metrics = {"error": "metrics_unavailable"}
        
        metrics = {
            "timestamp": current_time,
            "database": db_metrics,
            "redis": redis_metrics,
            "nodes": node_metrics,
            "api": {
                "uptime_seconds": 0,  # Would track actual uptime
                "requests_last_hour": 0,  # Would track from middleware
                "average_response_time_ms": 0  # Would track from middleware
            }
        }
        
        return APIResponse(
            success=True,
            data=metrics,
            message="System metrics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"System metrics failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "metrics_failed",
                "message": "Failed to retrieve system metrics"
            }
        )

@router.get(
    "/readiness",
    response_model=APIResponse,
    summary="Readiness Check",
    description="Check if the service is ready to handle requests"
)
async def readiness_check(db: Session = Depends(get_async_db)):
    """Check if service is ready to handle requests"""
    try:
        # Check database connection
        db.execute(text("SELECT 1"))
        
        # Check Redis connection
        await redis_manager.ping()
        
        return APIResponse(
            success=True,
            data={
                "status": "ready",
                "timestamp": datetime.utcnow()
            },
            message="Service is ready to handle requests"
        )
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "service_not_ready",
                "message": "Service is not ready to handle requests"
            }
        )

@router.get(
    "/liveness",
    response_model=APIResponse,
    summary="Liveness Check",
    description="Check if the service is alive (for container orchestration)"
)
async def liveness_check():
    """Check if service is alive (minimal check for container orchestration)"""
    return APIResponse(
        success=True,
        data={
            "status": "alive",
            "timestamp": datetime.utcnow()
        },
        message="Service is alive"
    )

@router.get("/stats/nodes")
async def get_node_statistics(
    db: Session = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """Get node statistics for admin dashboard"""
    try:
        # Count nodes by status
        total_nodes = db.query(Node).count()
        active_nodes = db.query(Node).filter(Node.status == NodeStatus.active).count()
        inactive_nodes = db.query(Node).filter(Node.status == NodeStatus.inactive).count()
        error_nodes = db.query(Node).filter(Node.status == NodeStatus.error).count()
        
        # Count sensors and actuators
        total_sensors = db.query(Sensor).count()
        total_actuators = db.query(Actuator).count()
        
        return {
            "total_nodes": total_nodes,
            "active_nodes": active_nodes,
            "inactive_nodes": inactive_nodes,
            "error_nodes": error_nodes,
            "total_sensors": total_sensors,
            "total_actuators": total_actuators,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting node statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get node statistics"
        )
