"""
Smart Greenhouse IoT System - Actuator Control Routes
Handles actuator registration, control commands, and monitoring
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer
from sqlalchemy import select, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import uuid

from database import get_db
from auth import require_api_key, require_node_object, get_current_user
from models import (
    ActuatorEvent, Actuator, Node, User, 
    ActuatorType
)
from schemas import (
    ActuatorCreate, ActuatorUpdate, ActuatorResponse,
    ActuatorCommandCreate, ActuatorCommandResponse,
    ActuatorTypeEnum
)

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

@router.post("/actuators", response_model=ActuatorResponse, status_code=status.HTTP_201_CREATED)
async def register_actuator(
    actuator: ActuatorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Register a new actuator in the system
    Requires: manager or admin role
    """
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to register actuators"
        )
    
    try:
        # Check if node exists
        node_query = select(Node).where(Node.node_id == actuator.node_id)
        node_result = await db.execute(node_query)
        node = node_result.scalar_one_or_none()
        
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Node {actuator.node_id} not found"
            )
        
        # Create new actuator
        db_actuator = Actuator(
            actuator_id=str(uuid.uuid4()),
            node_id=actuator.node_id,
            zone_id=actuator.zone_id,
            actuator_type=actuator.actuator_type,
            pin_number=actuator.pin_number,
            max_runtime_seconds=actuator.max_runtime_seconds or 300,
            description=actuator.description,
            is_active=True,
            current_state=False
        )
        
        db.add(db_actuator)
        await db.commit()
        await db.refresh(db_actuator)
        
        logger.info(f"Actuator {db_actuator.actuator_id} registered for node {actuator.node_id}")
        
        return db_actuator
        
    except Exception as e:
        logger.error(f"Error registering actuator: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register actuator: {str(e)}"
        )

@router.get("/actuators", response_model=List[ActuatorResponse])
async def list_actuators(
    node_id: Optional[str] = Query(None),
    zone_id: Optional[str] = Query(None),
    actuator_type: Optional[ActuatorTypeEnum] = Query(None),
    active_only: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    List actuators for authenticated node
    """
    try:
        query = select(Actuator).where(Actuator.node_id == node.node_id)
        
        if zone_id:
            query = query.where(Actuator.zone_id == zone_id)
        if actuator_type:
            query = query.where(Actuator.actuator_type == actuator_type)
        if active_only:
            query = query.where(Actuator.is_active == True)
        
        result = await db.execute(query)
        actuators = result.scalars().all()
        
        return actuators
        
    except Exception as e:
        logger.error(f"Error listing actuators: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list actuators: {str(e)}"
        )

@router.post("/actuators/{actuator_id}/control", response_model=ActuatorCommandResponse)
async def control_actuator(
    actuator_id: str,
    command: ActuatorCommandCreate,
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Control an actuator (turn on/off, set duration)
    """
    try:
        # Find actuator
        actuator_query = select(Actuator).where(
            and_(
                Actuator.actuator_id == actuator_id,
                Actuator.node_id == node.node_id,
                Actuator.is_active == True
            )
        )
        result = await db.execute(actuator_query)
        actuator = result.scalar_one_or_none()
        
        if not actuator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Actuator {actuator_id} not found"
            )
        
        # Create actuator event
        event = ActuatorEvent(
            time=command.timestamp or datetime.utcnow(),
            node_id=node.node_id,
            zone_id=actuator.zone_id,
            actuator_id=actuator_id,
            command=command.command,
            state=command.command.lower() == "on",
            duration_seconds=command.duration_minutes * 60 if command.duration_minutes else None,
            triggered_by=f"node_{node.node_id}",
            reason="Remote control command",
            meta_data={"value": command.value} if command.value else {}
        )
        
        # Update actuator state
        actuator.current_state = event.state
        actuator.updated_at = datetime.utcnow()
        
        db.add(event)
        await db.commit()
        
        logger.info(f"Actuator {actuator_id} controlled: {command.command}")
        
        return {
            "actuator_id": actuator_id,
            "command": command.command,
            "state": event.state,
            "duration_seconds": event.duration_seconds,
            "timestamp": event.time.isoformat() + "Z",
            "safety_check": "passed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error controlling actuator {actuator_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to control actuator: {str(e)}"
        )

@router.get("/actuators/{actuator_id}/status", response_model=dict)
async def get_actuator_status(
    actuator_id: str,
    db: AsyncSession = Depends(get_db),
    node: Node = Depends(require_node_object)
):
    """
    Get current actuator status and recent activity
    """
    try:
        # Find actuator
        actuator_query = select(Actuator).where(
            and_(
                Actuator.actuator_id == actuator_id,
                Actuator.node_id == node.node_id
            )
        )
        result = await db.execute(actuator_query)
        actuator = result.scalar_one_or_none()
        
        if not actuator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Actuator {actuator_id} not found"
            )
        
        # Get recent events
        events_query = select(ActuatorEvent).where(
            ActuatorEvent.actuator_id == actuator_id
        ).order_by(desc(ActuatorEvent.time)).limit(5)
        
        events_result = await db.execute(events_query)
        recent_events = events_result.scalars().all()
        
        # Calculate runtime today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        runtime_query = select(ActuatorEvent).where(
            and_(
                ActuatorEvent.actuator_id == actuator_id,
                ActuatorEvent.time >= today_start,
                ActuatorEvent.state == True
            )
        )
        
        runtime_result = await db.execute(runtime_query)
        runtime_events = runtime_result.scalars().all()
        
        total_runtime_today = sum(
            event.duration_seconds or 0 for event in runtime_events
        )
        
        return {
            "actuator_id": actuator_id,
            "current_state": actuator.current_state,
            "last_activated": recent_events[0].time.isoformat() + "Z" if recent_events else None,
            "total_runtime_today": total_runtime_today,
            "remaining_runtime": max(0, actuator.max_runtime_seconds - total_runtime_today),
            "recent_events": [
                {
                    "time": event.time.isoformat() + "Z",
                    "command": event.command,
                    "state": event.state,
                    "duration": event.duration_seconds
                }
                for event in recent_events
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting actuator status {actuator_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get actuator status: {str(e)}"
        )
