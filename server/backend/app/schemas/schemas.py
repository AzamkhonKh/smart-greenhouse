"""
Smart Greenhouse IoT System - Pydantic Schemas
Request/Response models for API validation and serialization
"""

from datetime import datetime, date
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
from enum import Enum

# Enums for validation
class UserRoleEnum(str, Enum):
    admin = "admin"
    manager = "manager"
    operator = "operator"
    viewer = "viewer"

class NodeStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"
    error = "error"

class SensorTypeEnum(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    soil_moisture = "soil_moisture"
    light = "light"
    ph = "ph"
    ec = "ec"
    battery_percentage = "battery_percentage"
    signal_strength = "signal_strength"
    voltage = "voltage"

class ActuatorTypeEnum(str, Enum):
    water_pump = "water_pump"
    ventilation_fan = "ventilation_fan"
    heater = "heater"
    cooler = "cooler"
    led_light = "led_light"
    valve = "valve"
    motor = "motor"

class ActuatorStatusEnum(str, Enum):
    on = "on"
    off = "off"
    auto = "auto"
    manual = "manual"

# Base schemas
class BaseSchema(BaseModel):
    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

# Authentication schemas
class UserLogin(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRoleEnum = UserRoleEnum.viewer

class UserUpdate(BaseModel):
    email: Optional[str] = Field(None, pattern=r'^[^@]+@[^@]+\.[^@]+$')
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    role: Optional[UserRoleEnum] = None
    is_active: Optional[bool] = None

class UserResponse(BaseSchema):
    user_id: str
    username: str
    email: str
    full_name: str
    role: UserRoleEnum
    is_active: bool
    created_at: datetime
    last_login: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# Node schemas
class NodeCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    zone_id: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None

class NodeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)
    zone_id: Optional[str] = None
    status: Optional[NodeStatusEnum] = None
    configuration: Optional[Dict[str, Any]] = None

class NodeResponse(BaseSchema):
    node_id: str
    name: str
    description: Optional[str]
    location: Optional[str]
    zone_id: Optional[str]
    status: NodeStatusEnum
    last_seen: Optional[datetime]
    configuration: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

class NodeStats(BaseModel):
    node_id: str
    uptime_percentage: float
    message_count_24h: int
    last_communication: Optional[datetime]
    sensor_count: int
    actuator_count: int

# Zone schemas
class ZoneCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    area_sqm: Optional[float] = Field(None, gt=0)
    crop_type: Optional[str] = Field(None, max_length=100)
    target_conditions: Optional[Dict[str, Any]] = None

class ZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    area_sqm: Optional[float] = Field(None, gt=0)
    crop_type: Optional[str] = Field(None, max_length=100)
    target_conditions: Optional[Dict[str, Any]] = None

class ZoneResponse(BaseSchema):
    zone_id: str
    name: str
    description: Optional[str]
    area_sqm: Optional[float]
    crop_type: Optional[str]
    target_conditions: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    node_count: Optional[int] = 0

# Sensor schemas
class SensorCreate(BaseModel):
    node_id: str
    sensor_type: SensorTypeEnum
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unit: str = Field(..., max_length=20)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    calibration_offset: Optional[float] = 0.0
    calibration_scale: Optional[float] = 1.0

class SensorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    unit: Optional[str] = Field(None, max_length=20)
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    calibration_offset: Optional[float] = None
    calibration_scale: Optional[float] = None
    is_active: Optional[bool] = None

class SensorResponse(BaseSchema):
    sensor_id: str
    node_id: str
    sensor_type: SensorTypeEnum
    name: str
    description: Optional[str]
    unit: str
    min_value: Optional[float]
    max_value: Optional[float]
    calibration_offset: float
    calibration_scale: float
    is_active: bool
    created_at: datetime
    updated_at: datetime
    latest_reading: Optional[float] = None
    latest_reading_time: Optional[datetime] = None

# Actuator schemas
class ActuatorCreate(BaseModel):
    node_id: str
    actuator_type: ActuatorTypeEnum
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    pin_number: Optional[int] = Field(None, ge=0, le=255)
    configuration: Optional[Dict[str, Any]] = None

class ActuatorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    pin_number: Optional[int] = Field(None, ge=0, le=255)
    configuration: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ActuatorControl(BaseModel):
    status: ActuatorStatusEnum
    value: Optional[float] = Field(None, ge=0, le=100)
    duration_minutes: Optional[int] = Field(None, gt=0)

class ActuatorResponse(BaseSchema):
    actuator_id: str
    node_id: str
    actuator_type: ActuatorTypeEnum
    name: str
    description: Optional[str]
    pin_number: Optional[int]
    configuration: Optional[Dict[str, Any]]
    is_active: bool
    current_status: ActuatorStatusEnum
    current_value: Optional[float]
    created_at: datetime
    updated_at: datetime
    last_control_time: Optional[datetime] = None

# Sensor reading schemas
class SensorReadingCreate(BaseModel):
    sensor_id: str
    value: float
    quality: Optional[float] = Field(None, ge=0, le=1)
    timestamp: Optional[datetime] = None

class SensorReadingBatch(BaseModel):
    readings: List[SensorReadingCreate] = Field(..., max_items=1000)

class SensorReadingResponse(BaseSchema):
    reading_id: str
    sensor_id: str
    value: float
    quality: float
    timestamp: datetime

# CoAP sensor data submission schema
class CoAPSensorData(BaseModel):
    """Schema for CoAP sensor data submissions from IoT nodes"""
    node_id: str = Field(..., description="Node ID submitting the data")
    zone_id: Optional[str] = Field(None, description="Zone ID (optional)")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    timestamp: Optional[datetime] = Field(None, description="Reading timestamp (ISO format)")
    
    # Sensor readings (all optional - node sends only available data)
    temperature: Optional[float] = Field(None, description="Temperature in °C")
    humidity: Optional[float] = Field(None, description="Humidity in %")
    soil_moisture: Optional[float] = Field(None, description="Soil moisture in %")
    light: Optional[int] = Field(None, description="Light in lux")
    ph: Optional[float] = Field(None, description="pH value")
    ec: Optional[float] = Field(None, description="Electrical conductivity in μS/cm")
    battery_percentage: Optional[float] = Field(None, description="Battery level in %")
    signal_strength: Optional[int] = Field(None, description="Signal strength in dBm")
    voltage: Optional[float] = Field(None, description="Supply voltage in V")
    
    # Metadata
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        if v and v.tzinfo is None:
            # Add UTC timezone if none specified
            from datetime import timezone
            return v.replace(tzinfo=timezone.utc)
        return v

# CoAP response schema
class CoAPResponse(BaseModel):
    """Schema for CoAP responses"""
    status: str = Field(..., description="Response status (success/error)")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(..., description="Response timestamp")
    readings_count: Optional[int] = Field(None, description="Number of readings processed")

# Actuator command schemas
class ActuatorCommandCreate(BaseModel):
    actuator_id: str
    command: str = Field(..., max_length=50)
    value: Optional[float] = None
    duration_minutes: Optional[int] = Field(None, gt=0)
    timestamp: Optional[datetime] = None

class ActuatorCommandResponse(BaseSchema):
    command_id: str
    actuator_id: str
    command: str
    value: Optional[float]
    duration_minutes: Optional[int]
    timestamp: datetime
    status: str

# Analytics and reporting schemas
class AnalyticsTimeRange(BaseModel):
    start_time: datetime
    end_time: datetime
    
    @field_validator('end_time')
    @classmethod
    def end_after_start(cls, v, info):
        if 'start_time' in info.data and v <= info.data['start_time']:
            raise ValueError('end_time must be after start_time')
        return v

class SensorAnalyticsRequest(BaseModel):
    sensor_ids: List[str] = Field(..., min_items=1, max_items=50)
    time_range: AnalyticsTimeRange
    aggregation: str = Field("hourly", pattern="^(minutely|hourly|daily|weekly)$")
    include_stats: bool = True

class SensorDataPoint(BaseModel):
    timestamp: datetime
    value: float
    quality: float

class SensorAnalyticsResponse(BaseModel):
    sensor_id: str
    sensor_name: str
    unit: str
    data_points: List[SensorDataPoint]
    statistics: Optional[Dict[str, float]] = None

class ZoneAnalyticsRequest(BaseModel):
    zone_ids: List[str] = Field(..., min_items=1, max_items=10)
    time_range: AnalyticsTimeRange
    metrics: List[str] = Field(..., min_items=1)

class ZoneMetrics(BaseModel):
    zone_id: str
    zone_name: str
    metrics: Dict[str, List[Dict[str, Any]]]

class SystemHealthResponse(BaseModel):
    timestamp: datetime
    total_nodes: int
    active_nodes: int
    inactive_nodes: int
    error_nodes: int
    total_sensors: int
    active_sensors: int
    sensor_uptime_percentage: float
    data_points_24h: int
    alerts_count: int
    system_status: str

# Alert schemas
class AlertCreate(BaseModel):
    sensor_id: str
    alert_type: str = Field(..., max_length=50)
    severity: str = Field("warning", pattern="^(info|warning|error|critical)$")
    message: str = Field(..., max_length=500)
    threshold_value: Optional[float] = None
    actual_value: Optional[float] = None

class AlertResponse(BaseSchema):
    alert_id: str
    sensor_id: str
    alert_type: str
    severity: str
    message: str
    threshold_value: Optional[float]
    actual_value: Optional[float]
    acknowledged: bool
    acknowledged_by: Optional[str]
    acknowledged_at: Optional[datetime]
    created_at: datetime

# Pagination schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: List[Any], total: int, page: int, size: int):
        pages = (total + size - 1) // size
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

# Error response schemas
class ErrorDetail(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None

class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    invalid_value: Optional[Any] = None

class ValidationErrorResponse(BaseModel):
    error: str = "validation_failed"
    message: str = "Request validation failed"
    validation_errors: List[ValidationErrorDetail]

# API Response wrapper
class APIResponse(BaseModel):
    success: bool = True
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class APIError(BaseModel):
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)
