"""
Smart Greenhouse IoT System - Sensor Data Routes
Handles sensor registration, data submission, and time-series queries
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query, Body
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, and_, desc, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid

from database import get_db
from auth import require_api_key, require_node_object, get_current_user
from models import (
    SensorReading, Sensor, Node, User, 
    SensorType, DataQuality
)
from schemas import (
    SensorCreate, SensorUpdate, SensorResponse,
    SensorReadingBatch, SensorTypeEnum
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# ============================================================================
# SENSOR MANAGEMENT ENDPOINTS
# ============================================================================

@router.post("/sensors", response_model=SensorResponse, status_code=status.HTTP_201_CREATED)
async def register_sensor(
    sensor: SensorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new sensor in the system
    Requires: manager or admin role
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to register sensors"
        )
    
    try:
        # Check if node exists
        node_query = select(Node).where(Node.node_id == sensor.node_id)
        node_result = await db.execute(node_query)
        node = node_result.scalar_one_or_none()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node {sensor.node_id} not found"
            )
        
        # Create new sensor
        db_sensor = Sensor(
            sensor_id=str(uuid.uuid4()),
            node_id=sensor.node_id,
            zone_id=sensor.zone_id,
            sensor_type=sensor.sensor_type,
            pin_number=sensor.pin_number,
            calibration_offset=sensor.calibration_offset or 0.0,
            calibration_multiplier=sensor.calibration_multiplier or 1.0,
            description=sensor.description,
            is_active=True
        )
        
        db.add(db_sensor)
        await db.commit()
        await db.refresh(db_sensor)
        
        logger.info(f"Sensor {db_sensor.sensor_id} registered for node {sensor.node_id}")
        
        return SensorResponse(
            sensor_id=db_sensor.sensor_id,
            node_id=db_sensor.node_id,
            zone_id=db_sensor.zone_id,
            sensor_type=db_sensor.sensor_type,
            pin_number=db_sensor.pin_number,
            calibration_offset=db_sensor.calibration_offset,
            calibration_multiplier=db_sensor.calibration_multiplier,
            description=db_sensor.description,
            is_active=db_sensor.is_active,
            created_at=db_sensor.created_at,
            updated_at=db_sensor.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error registering sensor: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register sensor: {str(e)}"
        )

@router.get("/sensors", response_model=List[SensorResponse])
async def list_sensors(
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    sensor_type: Optional[SensorTypeEnum] = Query(None, description="Filter by sensor type"),
    active_only: bool = Query(True, description="Show only active sensors"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all sensors with optional filtering
    """
    try:
        query = select(Sensor)
        
        # Apply filters
        if node_id:
            query = query.where(Sensor.node_id == node_id)
        if zone_id:
            query = query.where(Sensor.zone_id == zone_id)
        if sensor_type:
            query = query.where(Sensor.sensor_type == sensor_type)
        if active_only:
            query = query.where(Sensor.is_active == True)
        
        query = query.order_by(Sensor.node_id, Sensor.zone_id, Sensor.sensor_type)
        
        result = await db.execute(query)
        sensors = result.scalars().all()
        
        return [
            SensorResponse(
                sensor_id=sensor.sensor_id,
                node_id=sensor.node_id,
                zone_id=sensor.zone_id,
                sensor_type=sensor.sensor_type,
                pin_number=sensor.pin_number,
                calibration_offset=sensor.calibration_offset,
                calibration_multiplier=sensor.calibration_multiplier,
                description=sensor.description,
                is_active=sensor.is_active,
                created_at=sensor.created_at,
                updated_at=sensor.updated_at
            )
            for sensor in sensors
        ]
        
    except Exception as e:
        logger.error(f"Error listing sensors: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list sensors: {str(e)}"
        )

@router.get("/sensors/{sensor_id}", response_model=SensorResponse)
async def get_sensor(
    sensor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get sensor details by ID
    """
    try:
        query = select(Sensor).where(Sensor.sensor_id == sensor_id)
        result = await db.execute(query)
        sensor = result.scalar_one_or_none()
        
        if not sensor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor {sensor_id} not found"
            )
        
        return SensorResponse(
            sensor_id=sensor.sensor_id,
            node_id=sensor.node_id,
            zone_id=sensor.zone_id,
            sensor_type=sensor.sensor_type,
            pin_number=sensor.pin_number,
            calibration_offset=sensor.calibration_offset,
            calibration_multiplier=sensor.calibration_multiplier,
            description=sensor.description,
            is_active=sensor.is_active,
            created_at=sensor.created_at,
            updated_at=sensor.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sensor {sensor_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sensor: {str(e)}"
        )

@router.put("/sensors/{sensor_id}", response_model=SensorResponse)
async def update_sensor(
    sensor_id: str,
    sensor_update: SensorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update sensor configuration
    Requires: manager or admin role
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update sensors"
        )
    
    try:
        query = select(Sensor).where(Sensor.sensor_id == sensor_id)
        result = await db.execute(query)
        sensor = result.scalar_one_or_none()
        
        if not sensor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sensor {sensor_id} not found"
            )
        
        # Update fields
        update_data = sensor_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sensor, field, value)
        
        sensor.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(sensor)
        
        logger.info(f"Sensor {sensor_id} updated by {current_user.username}")
        
        return SensorResponse(
            sensor_id=sensor.sensor_id,
            node_id=sensor.node_id,
            zone_id=sensor.zone_id,
            sensor_type=sensor.sensor_type,
            pin_number=sensor.pin_number,
            calibration_offset=sensor.calibration_offset,
            calibration_multiplier=sensor.calibration_multiplier,
            description=sensor.description,
            is_active=sensor.is_active,
            created_at=sensor.created_at,
            updated_at=sensor.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating sensor {sensor_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sensor: {str(e)}"
        )

# ============================================================================
# SENSOR DATA SUBMISSION ENDPOINTS (Node API Key Required)
# ============================================================================

@router.post("/sensor-data", status_code=status.HTTP_201_CREATED)
async def submit_sensor_data(
    node_id: str = Body(..., description="Node ID submitting the data"),
    temperature: Optional[float] = Body(None, description="Temperature reading in °C"),
    humidity: Optional[float] = Body(None, description="Humidity reading in %"),
    soil_moisture: Optional[float] = Body(None, description="Soil moisture reading in %"),
    light: Optional[int] = Body(None, description="Light reading in lux"),
    ph: Optional[float] = Body(None, description="pH reading"),
    ec: Optional[float] = Body(None, description="Electrical conductivity in μS/cm"),
    battery_percentage: Optional[float] = Body(None, description="Battery level in %"),
    signal_strength: Optional[int] = Body(None, description="WiFi/signal strength in dBm"),
    voltage: Optional[float] = Body(None, description="Supply voltage in V"),
    timestamp: Optional[datetime] = Body(None, description="Reading timestamp (ISO format)"),
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Submit sensor readings from a node
    Simplified endpoint for node controllers
    """
    if node.node_id != node_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Node ID mismatch with API key"
        )
    
    try:
        readings_created = 0
        reading_time = timestamp or datetime.utcnow()
        
        # Map sensor data to readings
        sensor_data = {
            "temperature": temperature,
            "humidity": humidity,
            "soil_moisture": soil_moisture,
            "light": light,
            "ph": ph,
            "ec": ec,
            "battery_percentage": battery_percentage,
            "signal_strength": signal_strength,
            "voltage": voltage
        }
        
        for sensor_type, value in sensor_data.items():
            if value is not None:
                # Find sensor for this node and type
                sensor_query = select(Sensor).where(
                    and_(
                        Sensor.node_id == node_id,
                        Sensor.sensor_type == sensor_type,
                        Sensor.is_active == True
                    )
                ).limit(1)
                
                result = await db.execute(sensor_query)
                sensor = result.scalar_one_or_none()
                
                if sensor:
                    # Apply calibration
                    calibrated_value = (value * float(sensor.calibration_multiplier)) + float(sensor.calibration_offset)
                    
                    # Create sensor reading
                    reading = SensorReading(
                        time=reading_time,
                        node_id=node_id,
                        zone_id=sensor.zone_id,
                        sensor_id=sensor.sensor_id,
                        sensor_type=sensor_type,
                        value=calibrated_value,
                        unit=_get_sensor_unit(sensor_type),
                        quality=DataQuality.good,
                        meta_data={
                            "raw_value": value,
                            "calibrated": True,
                            "calibration_offset": float(sensor.calibration_offset),
                            "calibration_multiplier": float(sensor.calibration_multiplier),
                            "node_firmware": getattr(node, 'firmware_version', None),
                            "submission_time": datetime.utcnow().isoformat() + "Z"
                        }
                    )
                    
                    db.add(reading)
                    readings_created += 1
        
        await db.commit()
        
        logger.info(f"Node {node_id} submitted {readings_created} sensor readings")
        
        return {
            "status": "success",
            "data_points": readings_created,
            "timestamp": reading_time.isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error submitting sensor data from {node_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit sensor data: {str(e)}"
        )

@router.post("/sensor-data/batch", status_code=status.HTTP_201_CREATED)
async def submit_sensor_data_batch(
    batch: SensorReadingBatch,
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Submit multiple sensor readings in batch
    Optimized for high-frequency data collection
    """
    try:
        readings_created = 0
        
        for reading_data in batch.readings:
            # Verify sensor exists and belongs to this node
            sensor_query = select(Sensor).where(
                and_(
                    Sensor.sensor_id == reading_data.sensor_id,
                    Sensor.node_id == node.node_id,
                    Sensor.is_active == True
                )
            )
            
            result = await db.execute(sensor_query)
            sensor = result.scalar_one_or_none()
            
            if not sensor:
                logger.warning(f"Sensor {reading_data.sensor_id} not found for node {node.node_id}")
                continue
            
            # Apply calibration
            calibrated_value = (reading_data.value * float(sensor.calibration_multiplier)) + float(sensor.calibration_offset)
            
            # Create sensor reading
            reading = SensorReading(
                time=reading_data.timestamp or datetime.utcnow(),
                node_id=node.node_id,
                zone_id=sensor.zone_id,
                sensor_id=sensor.sensor_id,
                sensor_type=sensor.sensor_type,
                value=calibrated_value,
                unit=_get_sensor_unit(sensor.sensor_type),
                quality=DataQuality.good if reading_data.quality is None else DataQuality.good if reading_data.quality > 0.8 else DataQuality.poor,
                meta_data={"raw_value": reading_data.value, "calibrated": True, "quality_score": reading_data.quality}
            )
            
            db.add(reading)
            readings_created += 1
        
        await db.commit()
        
        logger.info(f"Node {node.node_id} submitted {readings_created} batch sensor readings")
        
        return {
            "status": "success",
            "readings_processed": len(batch.readings),
            "readings_created": readings_created,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error submitting batch sensor data from {node.node_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit batch sensor data: {str(e)}"
        )

# ============================================================================
# SENSOR DATA QUERY ENDPOINTS
# ============================================================================

@router.get("/sensor-data/latest")
async def get_latest_sensor_data(
    node_id: Optional[str] = Query(None, description="Filter by node ID"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    sensor_type: Optional[SensorTypeEnum] = Query(None, description="Filter by sensor type"),
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Get latest sensor readings for a node
    """
    try:
        # Build query for latest readings
        query = text("""
            SELECT DISTINCT ON (sensor_id) 
                time, node_id, zone_id, sensor_id, sensor_type, value, unit, quality
            FROM timeseries.sensor_readings
            WHERE node_id = :node_id
            AND (:zone_filter IS NULL OR zone_id = :zone_filter)
            AND (:type_filter IS NULL OR sensor_type = :type_filter)
            ORDER BY sensor_id, time DESC
        """)
        
        params = {
            "node_id": node.node_id,
            "zone_filter": zone_id,
            "type_filter": sensor_type.value if sensor_type else None
        }
        
        result = await db.execute(query, params)
        readings = result.fetchall()
        
        # Group readings by type for easy consumption
        data = {}
        for reading in readings:
            data[reading.sensor_type] = {
                "value": float(reading.value),
                "unit": reading.unit,
                "quality": reading.quality.value,
                "zone_id": reading.zone_id,
                "timestamp": reading.time.isoformat() + "Z"
            }
        
        return {
            "node_id": node.node_id,
            "readings": data,
            "reading_count": len(readings),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
    except Exception as e:
        logger.error(f"Error getting latest sensor data for {node.node_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get latest sensor data: {str(e)}"
        )

@router.get("/sensor-data/history")
async def get_sensor_data_history(
    start: datetime = Query(..., description="Start timestamp (ISO format)"),
    end: datetime = Query(..., description="End timestamp (ISO format)"),
    fields: Optional[str] = Query(None, description="Comma-separated sensor types"),
    interval: Optional[str] = Query("1h", description="Aggregation interval (1m, 5m, 15m, 1h, 1d)"),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    aggregation: str = Query("avg", description="Aggregation function (avg, min, max, sum)"),
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Get historical sensor data with time-series aggregation
    Powered by TimescaleDB for high-performance queries
    """
    try:
        # Validate interval
        valid_intervals = ["1m", "5m", "15m", "30m", "1h", "6h", "12h", "1d"]
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid interval. Use one of: {', '.join(valid_intervals)}"
            )
        
        # Validate aggregation
        valid_aggs = ["avg", "min", "max", "sum", "count"]
        if aggregation not in valid_aggs:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid aggregation. Use one of: {', '.join(valid_aggs)}"
            )
        
        # Parse sensor types
        sensor_types = []
        if fields:
            sensor_types = [t.strip() for t in fields.split(",")]
        
        # Build dynamic query
        where_clauses = ["node_id = :node_id", "time >= :start_time", "time <= :end_time"]
        params = {
            "node_id": node.node_id,
            "start_time": start,
            "end_time": end
        }
        
        if zone_id:
            where_clauses.append("zone_id = :zone_id")
            params["zone_id"] = zone_id
            
        if sensor_types:
            where_clauses.append("sensor_type = ANY(:sensor_types)")
            params["sensor_types"] = sensor_types
        
        where_clause = " AND ".join(where_clauses)
        
        query = text(f"""
            SELECT 
                time_bucket(:interval, time) as time_bucket,
                sensor_type,
                {aggregation}(value) as value,
                count(*) as data_points
            FROM timeseries.sensor_readings
            WHERE {where_clause}
            GROUP BY time_bucket, sensor_type
            ORDER BY time_bucket, sensor_type
        """)
        
        params["interval"] = interval
        
        result = await db.execute(query, params)
        rows = result.fetchall()
        
        # Format response
        data = []
        for row in rows:
            data.append({
                "timestamp": row.time_bucket.isoformat() + "Z",
                "sensor_type": row.sensor_type,
                "value": float(row.value),
                "data_points": row.data_points
            })
        
        return {
            "data": data,
            "aggregation": aggregation,
            "interval": interval,
            "total_points": len(data),
            "query_time_ms": 0,  # Could add timing if needed
            "node_id": node.node_id,
            "time_range": {
                "start": start.isoformat() + "Z",
                "end": end.isoformat() + "Z"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sensor history for {node.node_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sensor history: {str(e)}"
        )

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_sensor_unit(sensor_type: str) -> str:
    """Get the standard unit for a sensor type"""
    units = {
        "temperature": "°C",
        "humidity": "%",
        "soil_moisture": "%",
        "light": "lux",
        "ph": "pH",
        "ec": "μS/cm",
        "battery_percentage": "%",
        "signal_strength": "dBm",
        "voltage": "V"
    }
    return units.get(sensor_type, "")
