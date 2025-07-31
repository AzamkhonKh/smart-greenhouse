"""
Smart Greenhouse IoT System - Nodes Router
Node management, registration, and communication endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from database import get_async_db
from auth import get_current_user, get_current_node, require_role, UserRole
from schemas import (
    NodeCreate, NodeUpdate, NodeResponse, NodeStats,
    APIResponse, PaginationParams, PaginatedResponse
)
from models import Node, Sensor, Actuator, Zone, NodeStatus
from redis_utils import redis_manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/nodes",
    tags=["Node Management"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Insufficient permissions"},
        404: {"description": "Node not found"}
    }
)

@router.get(
    "/",
    response_model=PaginatedResponse,
    summary="List Nodes",
    description="Get paginated list of all nodes with optional filtering"
)
async def list_nodes(
    pagination: PaginationParams = Depends(),
    zone_id: Optional[str] = Query(None, description="Filter by zone ID"),
    status: Optional[NodeStatus] = Query(None, description="Filter by node status"),
    search: Optional[str] = Query(None, description="Search in name, location, or description"),
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.viewer))
):
    """Get paginated list of nodes with filtering"""
    try:
        query = db.query(Node)
        
        # Apply filters
        filters = []
        if zone_id:
            filters.append(Node.zone_id == zone_id)
        if status:
            filters.append(Node.status == status)
        if search:
            search_filter = or_(
                Node.name.ilike(f"%{search}%"),
                Node.location.ilike(f"%{search}%"),
                Node.description.ilike(f"%{search}%")
            )
            filters.append(search_filter)
        
        if filters:
            query = query.filter(and_(*filters))
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        nodes = query.offset(offset).limit(pagination.size).all()
        
        # Convert to response format
        node_responses = []
        for node in nodes:
            node_response = NodeResponse(
                node_id=node.node_id,
                name=node.name,
                description=node.description,
                location=node.location,
                zone_id=node.zone_id,
                status=node.status,
                last_seen=node.last_seen,
                configuration=node.configuration,
                created_at=node.created_at,
                updated_at=node.updated_at
            )
            node_responses.append(node_response)
        
        return PaginatedResponse.create(
            items=node_responses,
            total=total,
            page=pagination.page,
            size=pagination.size
        )
        
    except Exception as e:
        logger.error(f"List nodes failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "list_nodes_failed",
                "message": "Failed to retrieve nodes"
            }
        )

@router.post(
    "/",
    response_model=APIResponse,
    summary="Create Node",
    description="Create a new node (manager role required)"
)
async def create_node(
    node_data: NodeCreate,
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.manager))
):
    """Create a new node"""
    try:
        # Validate zone exists if provided
        if node_data.zone_id:
            zone = db.query(Zone).filter(Zone.zone_id == node_data.zone_id).first()
            if not zone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "zone_not_found",
                        "message": f"Zone {node_data.zone_id} not found"
                    }
                )
        
        # Create new node
        new_node = Node(
            name=node_data.name,
            description=node_data.description,
            location=node_data.location,
            zone_id=node_data.zone_id,
            status=NodeStatus.inactive,
            configuration=node_data.configuration or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(new_node)
        db.commit()
        db.refresh(new_node)
        
        logger.info(f"Node created: {new_node.node_id} by {current_user.username}")
        
        node_response = NodeResponse(
            node_id=new_node.node_id,
            name=new_node.name,
            description=new_node.description,
            location=new_node.location,
            zone_id=new_node.zone_id,
            status=new_node.status,
            last_seen=new_node.last_seen,
            configuration=new_node.configuration,
            created_at=new_node.created_at,
            updated_at=new_node.updated_at
        )
        
        return APIResponse(
            success=True,
            data=node_response,
            message="Node created successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create node failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "create_node_failed",
                "message": "Failed to create node"
            }
        )

@router.get(
    "/{node_id}",
    response_model=NodeResponse,
    summary="Get Node",
    description="Get detailed information about a specific node"
)
async def get_node(
    node_id: str,
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.viewer))
):
    """Get detailed node information"""
    try:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {node_id} not found"
                }
            )
        
        return NodeResponse(
            node_id=node.node_id,
            name=node.name,
            description=node.description,
            location=node.location,
            zone_id=node.zone_id,
            status=node.status,
            last_seen=node.last_seen,
            configuration=node.configuration,
            created_at=node.created_at,
            updated_at=node.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_node_failed",
                "message": "Failed to retrieve node"
            }
        )

@router.put(
    "/{node_id}",
    response_model=APIResponse,
    summary="Update Node",
    description="Update node information (manager role required)"
)
async def update_node(
    node_id: str,
    node_update: NodeUpdate,
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.manager))
):
    """Update node information"""
    try:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {node_id} not found"
                }
            )
        
        # Validate zone if being updated
        if node_update.zone_id:
            zone = db.query(Zone).filter(Zone.zone_id == node_update.zone_id).first()
            if not zone:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": "zone_not_found",
                        "message": f"Zone {node_update.zone_id} not found"
                    }
                )
        
        # Update fields
        if node_update.name is not None:
            node.name = node_update.name
        if node_update.description is not None:
            node.description = node_update.description
        if node_update.location is not None:
            node.location = node_update.location
        if node_update.zone_id is not None:
            node.zone_id = node_update.zone_id
        if node_update.status is not None:
            node.status = node_update.status
        if node_update.configuration is not None:
            node.configuration = node_update.configuration
        
        node.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(node)
        
        logger.info(f"Node updated: {node_id} by {current_user.username}")
        
        node_response = NodeResponse(
            node_id=node.node_id,
            name=node.name,
            description=node.description,
            location=node.location,
            zone_id=node.zone_id,
            status=node.status,
            last_seen=node.last_seen,
            configuration=node.configuration,
            created_at=node.created_at,
            updated_at=node.updated_at
        )
        
        return APIResponse(
            success=True,
            data=node_response,
            message="Node updated successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update node failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "update_node_failed",
                "message": "Failed to update node"
            }
        )

@router.delete(
    "/{node_id}",
    response_model=APIResponse,
    summary="Delete Node",
    description="Delete a node and all associated sensors/actuators (admin role required)"
)
async def delete_node(
    node_id: str,
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.admin))
):
    """Delete node and all associated components"""
    try:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {node_id} not found"
                }
            )
        
        # Check for associated sensors and actuators
        sensor_count = db.query(Sensor).filter(Sensor.node_id == node_id).count()
        actuator_count = db.query(Actuator).filter(Actuator.node_id == node_id).count()
        
        if sensor_count > 0 or actuator_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "node_has_components",
                    "message": f"Node has {sensor_count} sensors and {actuator_count} actuators. Remove them first."
                }
            )
        
        db.delete(node)
        db.commit()
        
        logger.info(f"Node deleted: {node_id} by {current_user.username}")
        
        return APIResponse(
            success=True,
            message="Node deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete node failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "delete_node_failed",
                "message": "Failed to delete node"
            }
        )

@router.get(
    "/{node_id}/stats",
    response_model=NodeStats,
    summary="Get Node Statistics",
    description="Get detailed statistics for a specific node"
)
async def get_node_stats(
    node_id: str,
    days: int = Query(7, ge=1, le=30, description="Number of days for statistics"),
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.viewer))
):
    """Get node statistics and health metrics"""
    try:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {node_id} not found"
                }
            )
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # Count sensors and actuators
        sensor_count = db.query(Sensor).filter(Sensor.node_id == node_id).count()
        actuator_count = db.query(Actuator).filter(Actuator.node_id == node_id).count()
        
        # Calculate uptime percentage (mock calculation)
        uptime_percentage = 85.5  # Would calculate from actual communication logs
        
        # Get message count (mock - would be from actual message logs)
        message_count_24h = 1440  # Would query from communication logs
        
        return NodeStats(
            node_id=node_id,
            uptime_percentage=uptime_percentage,
            message_count_24h=message_count_24h,
            last_communication=node.last_seen,
            sensor_count=sensor_count,
            actuator_count=actuator_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node stats failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_node_stats_failed",
                "message": "Failed to retrieve node statistics"
            }
        )

@router.post(
    "/heartbeat",
    response_model=APIResponse,
    summary="Node Heartbeat",
    description="Update node status and last seen timestamp (API key required)"
)
async def node_heartbeat(
    status_data: dict = None,
    current_node_id: str = Depends(get_current_node),
    db: Session = Depends(get_async_db)
):
    """Update node heartbeat and status"""
    try:
        node = db.query(Node).filter(Node.node_id == current_node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {current_node_id} not found"
                }
            )
        
        # Update last seen
        node.last_seen = datetime.utcnow()
        
        # Update status if node was inactive
        if node.status == NodeStatus.inactive:
            node.status = NodeStatus.active
        
        # Update configuration if provided
        if status_data:
            current_config = node.configuration or {}
            current_config.update(status_data)
            node.configuration = current_config
        
        node.updated_at = datetime.utcnow()
        db.commit()
        
        # Cache heartbeat in Redis
        await redis_manager.cache_node_heartbeat(current_node_id, datetime.utcnow())
        
        return APIResponse(
            success=True,
            data={
                "node_id": current_node_id,
                "status": node.status.value,
                "last_seen": node.last_seen
            },
            message="Heartbeat recorded"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Node heartbeat failed: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "heartbeat_failed",
                "message": "Failed to record heartbeat"
            }
        )

@router.get(
    "/{node_id}/sensors",
    response_model=List[dict],
    summary="Get Node Sensors",
    description="Get all sensors attached to a specific node"
)
async def get_node_sensors(
    node_id: str,
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.viewer))
):
    """Get all sensors for a node"""
    try:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {node_id} not found"
                }
            )
        
        sensors = db.query(Sensor).filter(Sensor.node_id == node_id).all()
        
        sensor_list = []
        for sensor in sensors:
            sensor_dict = {
                "sensor_id": sensor.sensor_id,
                "sensor_type": sensor.sensor_type.value,
                "name": sensor.name,
                "description": sensor.description,
                "unit": sensor.unit,
                "is_active": sensor.is_active,
                "created_at": sensor.created_at
            }
            sensor_list.append(sensor_dict)
        
        return sensor_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node sensors failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_node_sensors_failed",
                "message": "Failed to retrieve node sensors"
            }
        )

@router.get(
    "/{node_id}/actuators",
    response_model=List[dict],
    summary="Get Node Actuators",
    description="Get all actuators attached to a specific node"
)
async def get_node_actuators(
    node_id: str,
    db: Session = Depends(get_async_db),
    current_user = Depends(require_role(UserRole.viewer))
):
    """Get all actuators for a node"""
    try:
        node = db.query(Node).filter(Node.node_id == node_id).first()
        if not node:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "node_not_found",
                    "message": f"Node {node_id} not found"
                }
            )
        
        actuators = db.query(Actuator).filter(Actuator.node_id == node_id).all()
        
        actuator_list = []
        for actuator in actuators:
            actuator_dict = {
                "actuator_id": actuator.actuator_id,
                "actuator_type": actuator.actuator_type.value,
                "name": actuator.name,
                "description": actuator.description,
                "current_status": actuator.current_status.value,
                "is_active": actuator.is_active,
                "created_at": actuator.created_at
            }
            actuator_list.append(actuator_dict)
        
        return actuator_list
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get node actuators failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "get_node_actuators_failed",
                "message": "Failed to retrieve node actuators"
            }
        )
