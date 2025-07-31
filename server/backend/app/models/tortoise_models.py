"""
Smart Greenhouse IoT System - Tortoise ORM Models
Models for FastAPI Admin integration
"""

from tortoise.models import Model
from tortoise import fields
from datetime import datetime
from enum import Enum


class NodeStatus(str, Enum):
    active = "active"
    inactive = "inactive"
    maintenance = "maintenance"
    error = "error"


class SensorType(str, Enum):
    temperature = "temperature"
    humidity = "humidity"
    soil_moisture = "soil_moisture"
    light = "light"
    ph = "ph"
    ec = "ec"


class ActuatorType(str, Enum):
    solenoid = "solenoid"
    pump = "pump"
    fan = "fan"
    heater = "heater"
    led = "led"
    valve = "valve"


class UserRole(str, Enum):
    admin = "admin"
    manager = "manager"
    operator = "operator"
    viewer = "viewer"


class Admin(Model):
    """Admin user model for FastAPI Admin authentication"""
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=50, unique=True, description="Admin username")
    password = fields.CharField(max_length=200, description="Hashed password")
    email = fields.CharField(max_length=100, unique=True, description="Email address")
    is_active = fields.BooleanField(default=True, description="Active status")
    is_superuser = fields.BooleanField(default=False, description="Superuser status")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "admin_users"

    def __str__(self):
        return self.username


class Zone(Model):
    """Greenhouse zone model"""
    zone_id = fields.CharField(max_length=10, pk=True, description="Zone identifier (e.g., A1, B2)")
    name = fields.CharField(max_length=100, description="Zone display name")
    row_number = fields.IntField(description="Grid row number (1-3)")
    column_number = fields.IntField(description="Grid column number (1-3)")
    plant_type = fields.CharField(max_length=50, null=True, description="Type of plants in zone")
    planting_date = fields.DateField(null=True, description="Date when plants were planted")
    configuration = fields.JSONField(default=dict, description="Zone configuration as JSON")
    target_temperature = fields.DecimalField(max_digits=4, decimal_places=2, null=True, description="Target temperature")
    target_humidity = fields.DecimalField(max_digits=5, decimal_places=2, null=True, description="Target humidity")
    target_soil_moisture = fields.DecimalField(max_digits=5, decimal_places=2, null=True, description="Target soil moisture")
    irrigation_schedule = fields.CharField(max_length=255, null=True, description="Irrigation schedule")
    status = fields.CharField(max_length=20, default="active", description="Zone status")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "zones"
        table_description = "Greenhouse zones"
        ordering = ["zone_id"]

    def __str__(self):
        return f"{self.zone_id} - {self.name}"


class Node(Model):
    """Greenhouse controller node model"""
    node_id = fields.CharField(max_length=50, pk=True, description="Unique node identifier")
    name = fields.CharField(max_length=100, description="Node display name")
    location = fields.CharField(max_length=255, null=True, description="Physical location")
    node_type = fields.CharField(max_length=50, default="greenhouse", description="Node type")
    api_key = fields.CharField(max_length=255, unique=True, description="API key for authentication")
    status = fields.CharEnumField(
        NodeStatus,
        default=NodeStatus.active,
        description="Node operational status"
    )
    firmware_version = fields.CharField(max_length=20, null=True, description="Firmware version")
    configuration = fields.JSONField(default=dict, description="Node configuration as JSON")
    last_seen = fields.DatetimeField(null=True, description="Last communication timestamp")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "nodes"
        table_description = "Greenhouse controller nodes"
        ordering = ["node_id"]

    def __str__(self):
        return f"{self.node_id} - {self.name}"


class Sensor(Model):
    """Sensor model"""
    sensor_id = fields.UUIDField(pk=True, description="Unique sensor identifier")
    node_id = fields.CharField(max_length=50, description="Associated node ID")
    zone_id = fields.CharField(max_length=10, null=True, description="Zone ID where sensor is located")
    sensor_type = fields.CharEnumField(SensorType, description="Type of sensor")
    pin_number = fields.IntField(null=True, description="Pin number on the node")
    calibration_offset = fields.DecimalField(max_digits=10, decimal_places=4, default=0, description="Calibration offset")
    calibration_multiplier = fields.DecimalField(max_digits=10, decimal_places=4, default=1, description="Calibration multiplier")
    unit = fields.CharField(max_length=20, description="Measurement unit")
    min_value = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="Minimum expected value")
    max_value = fields.DecimalField(max_digits=10, decimal_places=4, null=True, description="Maximum expected value")
    is_active = fields.BooleanField(default=True, description="Sensor active status")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "sensors"
        table_description = "Greenhouse sensors"
        ordering = ["sensor_id"]

    def __str__(self):
        return f"{self.sensor_type} sensor on {self.node_id}"


class Actuator(Model):
    """Actuator model"""
    actuator_id = fields.CharField(max_length=50, pk=True, description="Unique actuator identifier")
    node_id = fields.CharField(max_length=50, description="Associated node ID")
    zone_id = fields.CharField(max_length=10, null=True, description="Zone ID where actuator is located")
    actuator_type = fields.CharEnumField(ActuatorType, description="Type of actuator")
    pin_number = fields.IntField(null=True, description="Pin number on the node")
    max_runtime_seconds = fields.IntField(default=300, description="Maximum runtime in seconds")
    safety_limits = fields.JSONField(default=dict, description="Safety limits as JSON")
    current_state = fields.BooleanField(default=False, description="Current actuator state")
    is_active = fields.BooleanField(default=True, description="Actuator active status")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "actuators"
        table_description = "Greenhouse actuators"
        ordering = ["actuator_id"]

    def __str__(self):
        return f"{self.actuator_type} actuator {self.actuator_id}"


class SensorReading(Model):
    """Sensor reading model for time-series data"""
    time = fields.DatetimeField(pk=True, description="Reading timestamp")
    node_id = fields.CharField(max_length=50, description="Associated node ID")
    zone_id = fields.CharField(max_length=10, null=True, description="Zone ID")
    sensor_id = fields.UUIDField(null=True, description="Sensor UUID")
    sensor_type = fields.CharEnumField(SensorType, description="Type of sensor")
    value = fields.DecimalField(max_digits=10, decimal_places=4, description="Sensor reading value")
    unit = fields.CharField(max_length=20, description="Measurement unit")
    quality = fields.CharField(max_length=20, default="good", description="Data quality indicator")
    metadata = fields.JSONField(default=dict, description="Additional metadata")

    class Meta:
        table = "sensor_readings"
        table_description = "Time-series sensor readings"
        ordering = ["-time"]

    def __str__(self):
        return f"{self.sensor_type} - {self.value} {self.unit} at {self.time}"


class ActuatorEvent(Model):
    """Actuator event model for control actions"""
    time = fields.DatetimeField(pk=True, description="Event timestamp")
    node_id = fields.CharField(max_length=50, description="Associated node ID")
    zone_id = fields.CharField(max_length=10, null=True, description="Zone ID")
    actuator_id = fields.CharField(max_length=50, description="Actuator ID")
    command = fields.CharField(max_length=50, description="Command sent to actuator")
    state = fields.BooleanField(description="Actuator state after command")
    duration_seconds = fields.IntField(null=True, description="Command duration in seconds")
    triggered_by = fields.CharField(max_length=100, null=True, description="What triggered this event")
    reason = fields.TextField(null=True, description="Reason for the command")
    metadata = fields.JSONField(default=dict, description="Additional metadata")

    class Meta:
        table = "actuator_events"
        table_description = "Time-series actuator events"
        ordering = ["-time"]

    def __str__(self):
        return f"{self.actuator_id} - {self.command} at {self.time}"
