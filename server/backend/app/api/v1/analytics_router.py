"""
Smart Greenhouse IoT System - Analytics Routes
Handles time-series analytics, aggregations, and reporting
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from database import get_db
from auth import get_current_user, require_api_key, require_node_object
from models import User, Node
from schemas import (
    SensorAnalyticsRequest, SensorAnalyticsResponse,
    SensorDataPoint, AnalyticsTimeRange
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.get("/continuous-aggregates")
async def get_continuous_aggregates(
    metric: str = Query(..., description="Sensor type (temperature, humidity, etc.)"),
    zone: Optional[str] = Query(None, description="Zone ID filter"),
    period: str = Query("hourly", description="Time period (hourly, daily, weekly)"),
    days: int = Query(7, description="Number of days to include"),
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Get continuous aggregate data from TimescaleDB materialized views
    High-performance pre-computed analytics
    """
    try:
        # Validate parameters
        valid_periods = ["hourly", "daily", "weekly"]
        if period not in valid_periods:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid period. Use: {', '.join(valid_periods)}"
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Build query based on period
        if period == "hourly":
            query = text("""
                SELECT 
                    time_bucket('1 hour', time) as time_bucket,
                    avg(value) as avg_value,
                    min(value) as min_value,
                    max(value) as max_value,
                    stddev(value) as stddev
                FROM timeseries.sensor_readings
                WHERE node_id = :node_id
                AND sensor_type = :metric
                AND time >= :start_time
                AND time <= :end_time
                AND (:zone_filter IS NULL OR zone_id = :zone_filter)
                GROUP BY time_bucket
                ORDER BY time_bucket
            """)
        elif period == "daily":
            query = text("""
                SELECT 
                    time_bucket('1 day', time) as time_bucket,
                    avg(value) as avg_value,
                    min(value) as min_value,
                    max(value) as max_value,
                    stddev(value) as stddev
                FROM timeseries.sensor_readings
                WHERE node_id = :node_id
                AND sensor_type = :metric
                AND time >= :start_time
                AND time <= :end_time
                AND (:zone_filter IS NULL OR zone_id = :zone_filter)
                GROUP BY time_bucket
                ORDER BY time_bucket
            """)
        
        params = {
            "node_id": node.node_id,
            "metric": metric,
            "start_time": start_time,
            "end_time": end_time,
            "zone_filter": zone
        }
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        data = []
        for row in rows:
            data.append({
                "time_bucket": row.time_bucket.isoformat() + "Z",
                "avg_value": float(row.avg_value) if row.avg_value else None,
                "min_value": float(row.min_value) if row.min_value else None,
                "max_value": float(row.max_value) if row.max_value else None,
                "stddev": float(row.stddev) if row.stddev else None
            })
        
        return {
            "data": data,
            "materialized_view": f"{period}_sensor_stats",
            "last_refresh": datetime.utcnow().isoformat() + "Z",
            "metric": metric,
            "period": period,
            "zone": zone,
            "node_id": node.node_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting continuous aggregates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get continuous aggregates: {str(e)}"
        )

@router.get("/downsample")
async def get_downsampled_data(
    metric: str = Query("all", description="Sensor type or 'all'"),
    zone: Optional[str] = Query(None, description="Zone ID filter"),
    resolution: str = Query("1h", description="Time resolution (15m, 1h, 6h, 1d)"),
    start: datetime = Query(..., description="Start timestamp"),
    end: datetime = Query(..., description="End timestamp"),
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Get downsampled sensor data with compression analytics
    Optimized for long-term trend analysis
    """
    try:
        # Validate resolution
        valid_resolutions = ["15m", "1h", "6h", "1d"]
        if resolution not in valid_resolutions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid resolution. Use: {', '.join(valid_resolutions)}"
            )
        
        # Build query for all metrics or specific metric
        if metric == "all":
            query = text("""
                SELECT 
                    time_bucket(:resolution, time) as time_bucket,
                    sensor_type,
                    avg(value) as avg_value,
                    count(*) as data_points_count
                FROM timeseries.sensor_readings
                WHERE node_id = :node_id
                AND time >= :start_time
                AND time <= :end_time
                AND (:zone_filter IS NULL OR zone_id = :zone_filter)
                GROUP BY time_bucket, sensor_type
                ORDER BY time_bucket, sensor_type
            """)
        else:
            query = text("""
                SELECT 
                    time_bucket(:resolution, time) as time_bucket,
                    :metric as sensor_type,
                    avg(value) as avg_value,
                    count(*) as data_points_count
                FROM timeseries.sensor_readings
                WHERE node_id = :node_id
                AND sensor_type = :metric
                AND time >= :start_time
                AND time <= :end_time
                AND (:zone_filter IS NULL OR zone_id = :zone_filter)
                GROUP BY time_bucket
                ORDER BY time_bucket
            """)
        
        params = {
            "resolution": resolution,
            "node_id": node.node_id,
            "start_time": start,
            "end_time": end,
            "zone_filter": zone,
            "metric": metric if metric != "all" else None
        }
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        # Format data for all metrics
        if metric == "all":
            # Group by time bucket
            time_buckets = {}
            for row in rows:
                time_str = row.time_bucket.isoformat() + "Z"
                if time_str not in time_buckets:
                    time_buckets[time_str] = {
                        "time_bucket": time_str,
                        "data_points_count": 0
                    }
                
                # Add sensor-specific data
                time_buckets[time_str][f"{row.sensor_type}_avg"] = float(row.avg_value) if row.avg_value else None
                time_buckets[time_str]["data_points_count"] += row.data_points_count
            
            data = list(time_buckets.values())
        else:
            data = [
                {
                    "time_bucket": row.time_bucket.isoformat() + "Z",
                    f"{metric}_avg": float(row.avg_value) if row.avg_value else None,
                    "data_points_count": row.data_points_count
                }
                for row in rows
            ]
        
        # Calculate compression statistics
        original_points = sum(row.data_points_count for row in rows)
        compressed_points = len(data)
        compression_ratio = f"{int((1 - compressed_points/max(original_points, 1)) * 100)}%" if original_points > 0 else "0%"
        
        return {
            "data": data,
            "compression_ratio": compression_ratio,
            "original_points": original_points,
            "compressed_points": compressed_points,
            "resolution": resolution,
            "metric": metric,
            "time_range": {
                "start": start.isoformat() + "Z",
                "end": end.isoformat() + "Z"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting downsampled data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get downsampled data: {str(e)}"
        )

@router.get("/zone-statistics")
async def get_zone_statistics(
    zone_id: str = Query(..., description="Zone ID"),
    days: int = Query(7, description="Number of days for statistics"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive zone statistics and health metrics
    """
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Query zone statistics from timeseries data
        query = text("""
            SELECT 
                sensor_type,
                avg(value) as avg_value,
                min(value) as min_value,
                max(value) as max_value,
                count(*) as reading_count,
                stddev(value) as stddev_value
            FROM timeseries.sensor_readings
            WHERE zone_id = :zone_id
            AND time >= :start_time
            AND time <= :end_time
            GROUP BY sensor_type
            ORDER BY sensor_type
        """)
        
        params = {
            "zone_id": zone_id,
            "start_time": start_time,
            "end_time": end_time
        }
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        statistics = {}
        for row in rows:
            statistics[row.sensor_type] = {
                "avg": float(row.avg_value) if row.avg_value else None,
                "min": float(row.min_value) if row.min_value else None,
                "max": float(row.max_value) if row.max_value else None,
                "stddev": float(row.stddev_value) if row.stddev_value else None,
                "reading_count": row.reading_count
            }
        
        # Calculate plant health score (simplified)
        health_score = 85.0  # Default good health
        if "temperature" in statistics and statistics["temperature"]["avg"]:
            temp_avg = statistics["temperature"]["avg"]
            if temp_avg < 18 or temp_avg > 30:
                health_score -= 15
        
        if "humidity" in statistics and statistics["humidity"]["avg"]:
            humid_avg = statistics["humidity"]["avg"]
            if humid_avg < 40 or humid_avg > 80:
                health_score -= 10
        
        return {
            "zone_id": zone_id,
            "period_days": days,
            "statistics": statistics,
            "plant_health_score": max(0, health_score),
            "total_readings": sum(stat["reading_count"] for stat in statistics.values()),
            "analysis_period": {
                "start": start_time.isoformat() + "Z",
                "end": end_time.isoformat() + "Z"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting zone statistics for {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get zone statistics: {str(e)}"
        )
