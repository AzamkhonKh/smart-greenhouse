"""
Smart Greenhouse IoT System - FastAPI Admin Configuration
Official FastAPI Admin setup with Tortoise ORM models
"""

import os
from fastapi import FastAPI
from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from fastapi_admin.resources import Field, Link, Model, Dropdown
from fastapi_admin.widgets import displays, filters, inputs
from fastapi_admin.file_upload import FileUpload
import aioredis

# Import Tortoise models
from tortoise_models import Admin, Zone, Node, Sensor, Actuator, SensorReading, ActuatorEvent, NodeStatus, SensorType, ActuatorType

# Base directory for static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File upload configuration
upload = FileUpload(uploads=os.path.join(BASE_DIR, "static", "uploads"))

# Login provider configuration
login_provider = UsernamePasswordProvider(
    admin_model=Admin,
    enable_captcha=False,  # Disable captcha for development
    login_logo_url="https://cdn.jsdelivr.net/npm/feather-icons@4.28.0/icons/home.svg"
)

async def setup_admin_interface(app: FastAPI):
    """Setup the FastAPI Admin interface with proper configuration"""
    try:
        # Create redis connection with newer API
        redis = aioredis.from_url(
            os.getenv("REDIS_URL", "redis://localhost:6379"),
            encoding="utf8",
            decode_responses=True
        )
        
        # Configure admin app
        admin_app.configure(
            logo_url="https://cdn.jsdelivr.net/npm/feather-icons@4.28.0/icons/home.svg",
            template_folders=[os.path.join(BASE_DIR, "templates")],
            providers=[login_provider],
            redis=redis,
        )
        
        print("FastAPI Admin interface configured successfully")
        
    except Exception as e:
        print(f"Warning: Could not configure admin interface: {e}")
        # Configure without Redis for development
        admin_app.configure(
            logo_url="https://cdn.jsdelivr.net/npm/feather-icons@4.28.0/icons/home.svg",
            template_folders=[os.path.join(BASE_DIR, "templates")],
            providers=[login_provider],
        )

import os
from fastapi import FastAPI
from fastapi_admin.app import app as admin_app
from fastapi_admin.providers.login import UsernamePasswordProvider
from fastapi_admin.resources import Field, Link, Model, Dropdown
from fastapi_admin.widgets import displays, filters, inputs
from fastapi_admin.file_upload import FileUpload
import aioredis

# Import Tortoise models
from tortoise_models import Admin, Zone, Node, Sensor, Actuator, SensorReading, ActuatorEvent, NodeStatus, SensorType, ActuatorType

# Base directory for static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# File upload configuration
upload = FileUpload(uploads=os.path.join(BASE_DIR, "static", "uploads"))

# Login provider configuration
login_provider = UsernamePasswordProvider(
    admin_model=Admin,
    enable_captcha=False,  # Disable captcha for development
    login_logo_url="https://cdn.jsdelivr.net/npm/feather-icons@4.28.0/icons/home.svg"
)


# Register Admin Links
@admin_app.register
class Dashboard(Link):
    label = "Dashboard"
    icon = "fas fa-tachometer-alt"
    url = "/admin"


# Register Zone Management
@admin_app.register
class ZoneResource(Model):
    label = "Zones"
    model = Zone
    icon = "fas fa-th-large"
    page_pre_title = "greenhouse management"
    page_title = "Zone Management"
    
    filters = [
        filters.Search(
            name="zone_id", 
            label="Zone ID", 
            search_mode="contains", 
            placeholder="Search zone ID"
        ),
        filters.Search(
            name="name", 
            label="Zone Name", 
            search_mode="contains", 
            placeholder="Search zone name"
        ),
        filters.Search(
            name="plant_type", 
            label="Plant Type", 
            search_mode="contains", 
            placeholder="Search plant type"
        ),
        filters.Search(
            name="status", 
            label="Status", 
            search_mode="exact"
        ),
    ]
    
    fields = [
        Field(name="zone_id", label="Zone ID"),
        Field(name="name", label="Zone Name"),
        Field(name="row_number", label="Row Number", input_=inputs.Number(step=1, minimum=1, maximum=3)),
        Field(name="column_number", label="Column Number", input_=inputs.Number(step=1, minimum=1, maximum=3)),
        Field(name="plant_type", label="Plant Type"),
        Field(name="planting_date", label="Planting Date", input_=inputs.Date()),
        Field(name="configuration", label="Configuration", display=displays.Json()),
        Field(
            name="target_temperature", 
            label="Target Temperature (°C)", 
            input_=inputs.Number(step=0.01)
        ),
        Field(
            name="target_humidity", 
            label="Target Humidity (%)", 
            input_=inputs.Number(step=0.01)
        ),
        Field(
            name="target_soil_moisture", 
            label="Target Soil Moisture (%)", 
            input_=inputs.Number(step=0.01)
        ),
        Field(name="irrigation_schedule", label="Irrigation Schedule"),
        Field(name="status", label="Status"),
        Field(name="created_at", label="Created", display=displays.Datetime()),
        Field(name="updated_at", label="Updated", display=displays.Datetime()),
    ]


# Register Node Management
@admin_app.register
class NodeResource(Model):
    label = "Nodes"
    model = Node
    icon = "fas fa-microchip"
    page_pre_title = "greenhouse management"
    page_title = "Node Management"
    
    filters = [
        filters.Search(
            name="node_id", 
            label="Node ID", 
            search_mode="contains", 
            placeholder="Search node ID"
        ),
        filters.Search(
            name="name", 
            label="Node Name", 
            search_mode="contains", 
            placeholder="Search node name"
        ),
        filters.Search(
            name="location", 
            label="Location", 
            search_mode="contains", 
            placeholder="Search location"
        ),
        filters.Enum(enum=NodeStatus, name="status", label="Status"),
        filters.Search(
            name="node_type", 
            label="Node Type", 
            search_mode="exact"
        ),
    ]
    
    fields = [
        Field(name="node_id", label="Node ID"),
        Field(name="name", label="Node Name"),
        Field(name="location", label="Location"),
        Field(name="node_type", label="Node Type"),
        Field(name="api_key", label="API Key", display=displays.InputOnly()),
        Field(
            name="status",
            label="Status",
            display=displays.Enum(),
            input_=inputs.Enum(enum=NodeStatus)
        ),
        Field(name="firmware_version", label="Firmware Version"),
        Field(name="configuration", label="Configuration", display=displays.Json()),
        Field(name="last_seen", label="Last Seen", display=displays.Datetime()),
        Field(name="created_at", label="Created", display=displays.Datetime()),
        Field(name="updated_at", label="Updated", display=displays.Datetime()),
    ]


# Register Sensor Management
@admin_app.register
class SensorResource(Model):
    label = "Sensors"
    model = Sensor
    icon = "fas fa-thermometer-half"
    page_pre_title = "iot devices"
    page_title = "Sensor Management"
    
    filters = [
        filters.Search(
            name="sensor_id", 
            label="Sensor ID", 
            search_mode="contains", 
            placeholder="Search sensor ID"
        ),
        filters.Enum(enum=SensorType, name="sensor_type", label="Sensor Type"),
        filters.Search(
            name="node_id", 
            label="Node ID", 
            search_mode="exact"
        ),
        filters.Search(
            name="zone_id", 
            label="Zone ID", 
            search_mode="exact"
        ),
        filters.Boolean(name="is_active", label="Active Status"),
    ]
    
    fields = [
        Field(name="sensor_id", label="Sensor ID"),
        Field(name="node_id", label="Node ID"),
        Field(name="zone_id", label="Zone ID"),
        Field(
            name="sensor_type",
            label="Type",
            display=displays.Enum(),
            input_=inputs.Enum(enum=SensorType)
        ),
        Field(
            name="pin_number",
            label="Pin Number",
            input_=inputs.Number(step=1, null=True)
        ),
        Field(
            name="calibration_offset",
            label="Calibration Offset",
            input_=inputs.Number(step=0.0001)
        ),
        Field(
            name="calibration_multiplier",
            label="Calibration Multiplier",
            input_=inputs.Number(step=0.0001)
        ),
        Field(name="unit", label="Unit"),
        Field(
            name="min_value",
            label="Min Value",
            input_=inputs.Number(step=0.0001, null=True)
        ),
        Field(
            name="max_value",
            label="Max Value",
            input_=inputs.Number(step=0.0001, null=True)
        ),
        Field(
            name="is_active",
            label="Active",
            display=displays.Boolean(),
            input_=inputs.Switch()
        ),
        Field(name="created_at", label="Created", display=displays.Datetime()),
        Field(name="updated_at", label="Updated", display=displays.Datetime()),
    ]


# Register Actuator Management
@admin_app.register
class ActuatorResource(Model):
    label = "Actuators"
    model = Actuator
    icon = "fas fa-cogs"
    page_pre_title = "iot devices"
    page_title = "Actuator Management"
    
    filters = [
        filters.Search(
            name="actuator_id", 
            label="Actuator ID", 
            search_mode="contains", 
            placeholder="Search actuator ID"
        ),
        filters.Enum(enum=ActuatorType, name="actuator_type", label="Actuator Type"),
        filters.Search(
            name="node_id", 
            label="Node ID", 
            search_mode="exact"
        ),
        filters.Search(
            name="zone_id", 
            label="Zone ID", 
            search_mode="exact"
        ),
        filters.Boolean(name="is_active", label="Active Status"),
        filters.Boolean(name="current_state", label="Current State"),
    ]
    
    fields = [
        Field(name="actuator_id", label="Actuator ID"),
        Field(name="node_id", label="Node ID"),
        Field(name="zone_id", label="Zone ID"),
        Field(
            name="actuator_type",
            label="Type",
            display=displays.Enum(),
            input_=inputs.Enum(enum=ActuatorType)
        ),
        Field(
            name="pin_number",
            label="Pin Number",
            input_=inputs.Number(step=1, null=True)
        ),
        Field(
            name="max_runtime_seconds",
            label="Max Runtime (s)",
            input_=inputs.Number(step=1)
        ),
        Field(name="safety_limits", label="Safety Limits", display=displays.Json()),
        Field(
            name="current_state",
            label="Current State",
            display=displays.Boolean(),
            input_=inputs.Switch()
        ),
        Field(
            name="is_active",
            label="Active",
            display=displays.Boolean(),
            input_=inputs.Switch()
        ),
        Field(name="created_at", label="Created", display=displays.Datetime()),
        Field(name="updated_at", label="Updated", display=displays.Datetime()),
    ]


# Register Data Management Dropdown
@admin_app.register
class DataManagement(Dropdown):
    label = "Data Management"
    icon = "fas fa-database"
    
    class SensorReadingResource(Model):
        label = "Sensor Readings"
        model = SensorReading
        page_title = "Sensor Data"
        
        filters = [
            filters.Search(
                name="node_id", 
                label="Node ID", 
                search_mode="exact"
            ),
            filters.Search(
                name="zone_id", 
                label="Zone ID", 
                search_mode="exact"
            ),
            filters.Enum(enum=SensorType, name="sensor_type", label="Sensor Type"),
            filters.Datetime(name="time", label="Timestamp"),
            filters.Search(name="quality", label="Quality"),
        ]
        
        fields = [
            Field(name="time", label="Timestamp", display=displays.Datetime()),
            Field(name="node_id", label="Node ID"),
            Field(name="zone_id", label="Zone ID"),
            Field(name="sensor_id", label="Sensor ID"),
            Field(
                name="sensor_type",
                label="Sensor Type",
                display=displays.Enum()
            ),
            Field(name="value", label="Value"),
            Field(name="unit", label="Unit"),
            Field(name="quality", label="Quality"),
            Field(name="metadata", label="Metadata", display=displays.Json()),
        ]
    
    class ActuatorEventResource(Model):
        label = "Actuator Events"
        model = ActuatorEvent
        page_title = "Actuator Control History"
        
        filters = [
            filters.Search(
                name="node_id", 
                label="Node ID", 
                search_mode="exact"
            ),
            filters.Search(
                name="zone_id", 
                label="Zone ID", 
                search_mode="exact"
            ),
            filters.Search(
                name="actuator_id", 
                label="Actuator ID", 
                search_mode="exact"
            ),
            filters.Datetime(name="time", label="Timestamp"),
            filters.Search(name="command", label="Command"),
            filters.Boolean(name="state", label="State"),
        ]
        
        fields = [
            Field(name="time", label="Timestamp", display=displays.Datetime()),
            Field(name="node_id", label="Node ID"),
            Field(name="zone_id", label="Zone ID"),
            Field(name="actuator_id", label="Actuator ID"),
            Field(name="command", label="Command"),
            Field(
                name="state",
                label="State",
                display=displays.Boolean()
            ),
            Field(name="duration_seconds", label="Duration (s)"),
            Field(name="triggered_by", label="Triggered By"),
            Field(name="reason", label="Reason", display=displays.Text()),
            Field(name="metadata", label="Metadata", display=displays.Json()),
        ]
    
    resources = [SensorReadingResource, ActuatorEventResource]


# Admin User Management
@admin_app.register
class AdminResource(Model):
    label = "Admin Users"
    model = Admin
    icon = "fas fa-users"
    page_pre_title = "system"
    page_title = "Admin User Management"
    
    filters = [
        filters.Search(
            name="username", 
            label="Username", 
            search_mode="contains", 
            placeholder="Search username"
        ),
        filters.Search(
            name="email", 
            label="Email", 
            search_mode="contains", 
            placeholder="Search email"
        ),
        filters.Boolean(name="is_active", label="Active"),
        filters.Boolean(name="is_superuser", label="Superuser"),
    ]
    
    fields = [
        "id",
        Field(name="username", label="Username"),
        Field(
            name="password",
            label="Password",
            display=displays.InputOnly(),
            input_=inputs.Password(),
        ),
        Field(name="email", label="Email", input_=inputs.Email()),
        Field(
            name="is_active",
            label="Active",
            display=displays.Boolean(),
            input_=inputs.Switch()
        ),
        Field(
            name="is_superuser",
            label="Superuser",
            display=displays.Boolean(),
            input_=inputs.Switch()
        ),
        "created_at",
        "updated_at",
    ]


async def setup_fastapi_admin(app: FastAPI):
    """Setup FastAPI Admin according to the quickstart guide"""
    
    # Configure Redis connection
    try:
        redis = await aioredis.create_redis_pool("redis://localhost:6379", encoding="utf8")
    except Exception as e:
        print(f"Redis connection failed: {e}, continuing without Redis")
        redis = None
    
    # Configure admin app
    admin_app.configure(
        logo_url="https://cdn.jsdelivr.net/npm/feather-icons@4.28.0/icons/home.svg",
        template_folders=[os.path.join(BASE_DIR, "templates")],
        providers=[login_provider],
        redis=redis,
        default_locale="en-US",
        language_switch=True,
        theme="light",
    )
    
    # Mount admin app
    app.mount("/admin", admin_app)
    
    return admin_app


def setup_admin_interface(app: FastAPI):
    """Wrapper for compatibility with existing code"""
    return setup_fastapi_admin(app)
