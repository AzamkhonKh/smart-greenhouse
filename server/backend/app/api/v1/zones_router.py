"""
Smart Greenhouse IoT System - Zone Management Routes  
Handles grid zone configuration and plant management
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db
from auth import get_current_user
from models import Zone, User
from schemas import (
    ZoneCreate, ZoneUpdate, ZoneResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.get("/zones", response_model=List[ZoneResponse])
async def list_zones(
    active_only: bool = Query(True, description="Show only active zones"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all greenhouse zones in the 3x3 grid
    """
    try:
        query = select(Zone)
        
        if active_only:
            query = query.where(Zone.is_active == True)
        
        query = query.order_by(Zone.row, Zone.column)
        
        result = await db.execute(query)
        zones = result.scalars().all()
        
        return [
            ZoneResponse(
                zone_id=zone.zone_id,
                name=zone.name,
                row=zone.row,
                column=zone.column,
                plant_type=zone.plant_type,
                planting_date=zone.planting_date,
                harvest_date=zone.harvest_date,
                irrigation_schedule=zone.irrigation_schedule,
                target_temperature=zone.target_temperature,
                target_humidity=zone.target_humidity,
                target_soil_moisture=zone.target_soil_moisture,
                is_active=zone.is_active,
                created_at=zone.created_at,
                updated_at=zone.updated_at
            )
            for zone in zones
        ]
        
    except Exception as e:
        logger.error(f"Error listing zones: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list zones: {str(e)}"
        )

@router.get("/zones/{zone_id}", response_model=ZoneResponse)
async def get_zone(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get zone details with sensor and actuator information
    """
    try:
        query = select(Zone).where(Zone.zone_id == zone_id)
        result = await db.execute(query)
        zone = result.scalar_one_or_none()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone {zone_id} not found"
            )
        
        return ZoneResponse(
            zone_id=zone.zone_id,
            name=zone.name,
            row=zone.row,
            column=zone.column,
            plant_type=zone.plant_type,
            planting_date=zone.planting_date,
            harvest_date=zone.harvest_date,
            irrigation_schedule=zone.irrigation_schedule,
            target_temperature=zone.target_temperature,
            target_humidity=zone.target_humidity,
            target_soil_moisture=zone.target_soil_moisture,
            is_active=zone.is_active,
            created_at=zone.created_at,
            updated_at=zone.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting zone {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get zone: {str(e)}"
        )

@router.put("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone(
    zone_id: str,
    zone_update: ZoneUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update zone configuration
    Requires: manager or admin role
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update zones"
        )
    
    try:
        query = select(Zone).where(Zone.zone_id == zone_id)
        result = await db.execute(query)
        zone = result.scalar_one_or_none()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone {zone_id} not found"
            )
        
        # Update fields
        update_data = zone_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(zone, field, value)
        
        zone.updated_at = datetime.utcnow()
        
        await db.commit()
        await db.refresh(zone)
        
        logger.info(f"Zone {zone_id} updated by {current_user.username}")
        
        return ZoneResponse(
            zone_id=zone.zone_id,
            name=zone.name,
            row=zone.row,
            column=zone.column,
            plant_type=zone.plant_type,
            planting_date=zone.planting_date,
            harvest_date=zone.harvest_date,
            irrigation_schedule=zone.irrigation_schedule,
            target_temperature=zone.target_temperature,
            target_humidity=zone.target_humidity,
            target_soil_moisture=zone.target_soil_moisture,
            is_active=zone.is_active,
            created_at=zone.created_at,
            updated_at=zone.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating zone {zone_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update zone: {str(e)}"
        )

@router.get("/zones/{zone_id}/config", response_model=dict)
async def get_zone_config(
    zone_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete zone configuration including sensors and actuators
    """
    try:
        # This would include more complex logic to fetch sensors, actuators, etc.
        # For now, return basic zone info
        query = select(Zone).where(Zone.zone_id == zone_id)
        result = await db.execute(query)
        zone = result.scalar_one_or_none()
        
        if not zone:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Zone {zone_id} not found"
            )
        
        return {
            "zone_id": zone.zone_id,
            "name": zone.name,
            "plant_type": zone.plant_type,
            "configuration": {
                "target_temperature": zone.target_temperature,
                "target_humidity": zone.target_humidity,
                "target_soil_moisture": zone.target_soil_moisture,
                "irrigation_schedule": zone.irrigation_schedule
            },
            "sensors": [],  # Would populate from sensor table
            "actuators": [],  # Would populate from actuator table
            "current_readings": {}  # Would get latest sensor data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting zone config {zone_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get zone config: {str(e)}"
        )
