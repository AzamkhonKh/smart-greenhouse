"""
Smart Greenhouse IoT System - Database Models
SQLAlchemy models for PostgreSQL and TimescaleDB
"""

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Text, JSON, 
    Enum, ForeignKey, Index, UniqueConstraint, Numeric
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
import uuid
import enum


Base = declarative_base()

# Enums
class UserRole(str, enum.Enum):
    admin = "admin"
    manager = "manager"
    operator = "operator"
    viewer = "viewer"

class NodeStatus(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"
    error = "error"

class SensorType(str, enum.Enum):
    temperature = "temperature"
    humidity = "humidity"
    soil_moisture = "soil_moisture"
    light = "light"
    ph = "ph"
    ec = "ec"
    battery_percentage = "battery_percentage"
    signal_strength = "signal_strength"
    voltage = "voltage"

class ActuatorType(str, enum.Enum):
    solenoid = "solenoid"
    pump = "pump"
    fan = "fan"
    heater = "heater"
    led = "led"
    valve = "valve"

class DataQuality(str, enum.Enum):
    good = "good"
    uncertain = "uncertain"
    bad = "bad"
    unknown = "unknown"

# Create enum types for PostgreSQL (commented out for string compatibility)
# sensor_type_enum = Enum(SensorType, name="sensor_type")
# actuator_type_enum = Enum(ActuatorType, name="actuator_type")
# data_quality_enum = Enum(DataQuality, name="data_quality")
# node_status_enum = Enum(NodeStatus, name="node_status")
# user_role_enum = Enum(UserRole, name="user_role")

# Main application tables
class User(Base):
    """User accounts with role-based access control"""
    __tablename__ = "users"
    __table_args__ = {"schema": "greenhouse"}
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default=UserRole.viewer.value, index=True)
    is_active = Column(Boolean, default=True, index=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    permissions = relationship("Permission", back_populates="user", foreign_keys="Permission.user_id", cascade="all, delete-orphan")
    granted_permissions = relationship("Permission", foreign_keys="Permission.granted_by")

class Node(Base):
    """Greenhouse controller nodes registry"""
    __tablename__ = "nodes"
    __table_args__ = {"schema": "greenhouse"}
    
    node_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(255))
    node_type = Column(String(50), nullable=False, default="greenhouse")
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    status = Column(String(20), default=NodeStatus.active.value, index=True)
    firmware_version = Column(String(20))
    configuration = Column(JSON, default={})
    last_seen = Column(DateTime(timezone=True), index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="node", cascade="all, delete-orphan")
    actuators = relationship("Actuator", back_populates="node", cascade="all, delete-orphan")
    rate_limits = relationship("RateLimit", back_populates="node", cascade="all, delete-orphan")

class Zone(Base):
    """3x3 grid zone definitions"""
    __tablename__ = "zones"
    __table_args__ = (
        UniqueConstraint('row_number', 'column_number'),
        {"schema": "greenhouse"}
    )
    
    zone_id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    row_number = Column(Integer, nullable=False)
    column_number = Column(Integer, nullable=False)
    plant_type = Column(String(50), index=True)
    planting_date = Column(DateTime(timezone=True))
    configuration = Column(JSON, default={})
    target_temperature = Column(Numeric(4, 2))
    target_humidity = Column(Numeric(5, 2))
    target_soil_moisture = Column(Numeric(5, 2))
    irrigation_schedule = Column(String(255))
    status = Column(String(20), default="active", index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sensors = relationship("Sensor", back_populates="zone")
    actuators = relationship("Actuator", back_populates="zone")

class Sensor(Base):
    """Sensor registry and configuration"""
    __tablename__ = "sensors"
    __table_args__ = (
        UniqueConstraint('node_id', 'pin_number'),
        {"schema": "greenhouse"}
    )
    
    sensor_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(String(50), ForeignKey("greenhouse.nodes.node_id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(String(10), ForeignKey("greenhouse.zones.zone_id", ondelete="SET NULL"), index=True)
    sensor_type = Column(Enum(SensorType, name="sensor_type", schema="greenhouse"), nullable=False, index=True)
    pin_number = Column(Integer)
    calibration_offset = Column(Numeric(10, 4), default=0)
    calibration_multiplier = Column(Numeric(10, 4), default=1)
    unit = Column(String(20), nullable=False)
    min_value = Column(Numeric(10, 4))
    max_value = Column(Numeric(10, 4))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="sensors")
    zone = relationship("Zone", back_populates="sensors")

class Actuator(Base):
    """Actuator configuration and safety limits"""
    __tablename__ = "actuators"
    __table_args__ = (
        UniqueConstraint('node_id', 'pin_number'),
        {"schema": "greenhouse"}
    )
    
    actuator_id = Column(String(50), primary_key=True)
    node_id = Column(String(50), ForeignKey("greenhouse.nodes.node_id", ondelete="CASCADE"), nullable=False, index=True)
    zone_id = Column(String(10), ForeignKey("greenhouse.zones.zone_id", ondelete="SET NULL"), index=True)
    actuator_type = Column(String(20), nullable=False, index=True)
    pin_number = Column(Integer)
    max_runtime_seconds = Column(Integer, default=300)
    safety_limits = Column(JSON, default={})
    current_state = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="actuators")
    zone = relationship("Zone", back_populates="actuators")

class Permission(Base):
    """Fine-grained access control matrix"""
    __tablename__ = "permissions"
    __table_args__ = (
        UniqueConstraint('user_id', 'resource_type', 'resource_id'),
        {"schema": "greenhouse"}
    )
    
    permission_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("greenhouse.users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    resource_type = Column(String(50), nullable=False, index=True)
    resource_id = Column(String(255))
    actions = Column(JSON, nullable=False)  # Array of allowed actions
    granted_by = Column(UUID(as_uuid=True), ForeignKey("greenhouse.users.user_id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    user = relationship("User", back_populates="permissions", foreign_keys=[user_id])
    granter = relationship("User", foreign_keys=[granted_by], overlaps="granted_permissions")

class SystemConfig(Base):
    """System configuration key-value store"""
    __tablename__ = "system_config"
    __table_args__ = {"schema": "greenhouse"}
    
    config_key = Column(String(100), primary_key=True)
    config_value = Column(JSON, nullable=False)
    description = Column(Text)
    updated_by = Column(UUID(as_uuid=True), ForeignKey("greenhouse.users.user_id"))
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

# Monitoring tables
class APILog(Base):
    """Complete audit trail for security and analytics"""
    __tablename__ = "api_logs"
    __table_args__ = {"schema": "monitoring"}
    
    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    node_id = Column(String(50), index=True)
    user_id = Column(UUID(as_uuid=True), index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, index=True)
    response_time_ms = Column(Integer)
    request_size = Column(Integer)
    response_size = Column(Integer)
    ip_address = Column(INET)
    user_agent = Column(Text)
    error_message = Column(Text)

class RateLimit(Base):
    """Per-node endpoint throttling configuration"""
    __tablename__ = "rate_limits"
    __table_args__ = (
        UniqueConstraint('node_id', 'endpoint'),
        {"schema": "monitoring"}
    )
    
    limit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(String(50), ForeignKey("greenhouse.nodes.node_id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False, index=True)
    requests_per_minute = Column(Integer, nullable=False, default=60)
    burst_limit = Column(Integer, nullable=False, default=10)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    node = relationship("Node", back_populates="rate_limits")

# TimescaleDB hypertables (time-series data)
class SensorReading(Base):
    """Time-series sensor measurements"""
    __tablename__ = "sensor_readings"
    __table_args__ = {"schema": "timeseries"}
    
    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(10), index=True)
    sensor_id = Column(UUID(as_uuid=True), index=True)
    sensor_type = Column(Enum(SensorType, name="sensor_type", schema="greenhouse"), nullable=False, index=True)
    value = Column(Numeric(10, 4), nullable=False)
    unit = Column(String(20), nullable=False)
    quality = Column(Enum(DataQuality, name="data_quality", schema="timeseries"), default=DataQuality.good, index=True)
    meta_data = Column("metadata", JSON, default={})

class ActuatorEvent(Base):
    """Control commands and state change history"""
    __tablename__ = "actuator_events"
    __table_args__ = {"schema": "timeseries"}
    
    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(10), index=True)
    actuator_id = Column(String(50), nullable=False, index=True)
    command = Column(String(50), nullable=False, index=True)
    state = Column(Boolean, nullable=False)
    duration_seconds = Column(Integer)
    triggered_by = Column(String(100))
    reason = Column(Text)
    meta_data = Column("metadata", JSON, default={})

class NodeHeartbeat(Base):
    """Node connectivity and health monitoring"""
    __tablename__ = "node_heartbeats"
    __table_args__ = {"schema": "timeseries"}
    
    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    node_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), nullable=False, index=True)
    uptime_seconds = Column(Integer)
    memory_usage_mb = Column(Integer)
    cpu_usage_percent = Column(Numeric(5, 2))
    signal_strength = Column(Integer)
    temperature = Column(Numeric(4, 2))
    free_storage_mb = Column(Integer)
    meta_data = Column("metadata", JSON, default={})

class ZoneAggregate(Base):
    """Pre-computed zone-level statistics"""
    __tablename__ = "zone_aggregates"
    __table_args__ = {"schema": "timeseries"}
    
    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    zone_id = Column(String(10), nullable=False, index=True)
    time_bucket_minutes = Column(Integer, nullable=False)
    avg_temperature = Column(Numeric(4, 2))
    min_temperature = Column(Numeric(4, 2))
    max_temperature = Column(Numeric(4, 2))
    avg_humidity = Column(Numeric(5, 2))
    min_humidity = Column(Numeric(5, 2))
    max_humidity = Column(Numeric(5, 2))
    avg_soil_moisture = Column(Numeric(5, 2))
    min_soil_moisture = Column(Numeric(5, 2))
    max_soil_moisture = Column(Numeric(5, 2))
    avg_light = Column(Integer)
    plant_health_score = Column(Numeric(3, 2))
    data_points_count = Column(Integer)
    meta_data = Column("metadata", JSON, default={})

class SystemMetric(Base):
    """System-wide performance and operational metrics"""
    __tablename__ = "system_metrics"
    __table_args__ = {"schema": "timeseries"}
    
    time = Column(DateTime(timezone=True), primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Numeric(15, 4), nullable=False)
    metric_unit = Column(String(20))
    node_id = Column(String(50), index=True)
    tags = Column(JSON, default={})

# Additional indexes for performance
Index('idx_sensor_readings_composite', SensorReading.node_id, SensorReading.sensor_type, SensorReading.time.desc())
Index('idx_actuator_events_composite', ActuatorEvent.node_id, ActuatorEvent.actuator_id, ActuatorEvent.time.desc())
Index('idx_node_heartbeats_node_time', NodeHeartbeat.node_id, NodeHeartbeat.time.desc())
Index('idx_system_metrics_name_time', SystemMetric.metric_name, SystemMetric.time.desc())
