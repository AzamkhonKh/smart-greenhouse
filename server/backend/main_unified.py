"""
Smart Greenhouse IoT System - Unified Main Application
Combines the simplicity of main_simple.py with the robustness of main.py
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
import asyncio
import json
import sys
from typing import Optional

# CoAP imports (conditional)
try:
    import aiocoap.resource as resource
    import aiocoap
    from aiocoap import Context, Message, Code
    COAP_AVAILABLE = True
except ImportError:
    COAP_AVAILABLE = False
    logging.warning("CoAP libraries not available - CoAP server will be disabled")

# Database imports (conditional)
try:
    from app.core.config import get_settings
    from app.db.database import init_db, close_db, test_db_connection
    from app.utils.redis_utils import init_redis, close_redis, test_redis_connection
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("Database modules not available - running in simple mode")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Global state
class AppState:
    coap_server: Optional['SimpleCoAPServer'] = None
    database_enabled: bool = False
    redis_enabled: bool = False

app_state = AppState()

# CoAP Server Implementation (if available)
if COAP_AVAILABLE:
    class SensorDataResource(resource.Resource):
        """CoAP resource for sensor data submission"""
        
        async def render_get(self, request):
            """Handle GET requests - provide endpoint info"""
            logger.info("📡 CoAP GET request received")
            
            info = {
                "service": "Smart Greenhouse CoAP Server",
                "version": "1.0.0",
                "endpoint": "/sensor/send-data",
                "methods": ["GET", "POST"],
                "auth": "Use query parameters: ?api_key=KEY&node_id=NODE_ID",
                "payload": "JSON with sensor values"
            }
            
            response_payload = json.dumps(info, indent=2).encode('utf-8')
            return Message(code=Code.CONTENT, payload=response_payload)
        
        async def render_post(self, request):
            """Handle POST requests - receive sensor data"""
            try:
                # Extract query parameters
                uri_query = ""
                if hasattr(request.opt, 'uri_query') and request.opt.uri_query:
                    if isinstance(request.opt.uri_query, bytes):
                        uri_query = request.opt.uri_query.decode('utf-8')
                    else:
                        uri_query = str(request.opt.uri_query)
                
                logger.info(f"📡 CoAP POST request. Query: {uri_query}")
                
                # Parse payload
                payload = request.payload.decode('utf-8') if request.payload else "{}"
                sensor_data = json.loads(payload)
                logger.info(f"📡 Sensor data: {sensor_data}")
                
                # Parse query parameters
                query_params = {}
                if uri_query:
                    for param in uri_query.split('&'):
                        if '=' in param:
                            key, value = param.split('=', 1)
                            query_params[key] = value
                
                # TODO: Save to database if available
                response = {
                    "status": "success",
                    "message": "Sensor data received via CoAP",
                    "timestamp": "2025-08-01T10:30:00Z",
                    "data_points": len(sensor_data),
                    "node_id": query_params.get('node_id', 'unknown'),
                    "authenticated": bool(query_params.get('api_key'))
                }
                
                response_payload = json.dumps(response).encode('utf-8')
                return Message(code=Code.CREATED, payload=response_payload)
                
            except json.JSONDecodeError:
                logger.error("📡 Invalid JSON in CoAP request")
                return Message(code=Code.BAD_REQUEST, payload=b"Invalid JSON")
            except Exception as e:
                logger.error(f"📡 CoAP error: {e}")
                return Message(code=Code.INTERNAL_SERVER_ERROR, payload=b"Server error")

    class SimpleCoAPServer:
        """CoAP server for IoT device communication"""
        
        def __init__(self):
            self.context = None
            self.running = False
        
        async def start(self):
            """Start the CoAP server"""
            try:
                logger.info("🚀 Starting CoAP server on port 5683...")
                
                root = resource.Site()
                root.add_resource(['sensor', 'send-data'], SensorDataResource())
                
                self.context = await Context.create_server_context(root, bind=('0.0.0.0', 5683))
                self.running = True
                
                logger.info("✅ CoAP server started on port 5683")
                
                # Keep running
                while self.running:
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ CoAP server failed: {e}")
                raise
        
        async def stop(self):
            """Stop the CoAP server"""
            self.running = False
            if self.context:
                await self.context.shutdown()
                logger.info("🔴 CoAP server stopped")

# Application lifecycle management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("🚀 Starting Smart Greenhouse IoT System...")
    
    # Initialize database if available
    if DATABASE_AVAILABLE:
        try:
            settings = get_settings()
            await test_db_connection()
            await init_db()
            app_state.database_enabled = True
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.warning(f"⚠️ Database unavailable: {e}")
    
    # Initialize Redis if available
    if DATABASE_AVAILABLE:
        try:
            await test_redis_connection()
            await init_redis()
            app_state.redis_enabled = True
            logger.info("✅ Redis initialized")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable: {e}")
    
    # Start CoAP server if available
    if COAP_AVAILABLE:
        try:
            app_state.coap_server = SimpleCoAPServer()
            asyncio.create_task(app_state.coap_server.start())
            logger.info("✅ CoAP server started")
        except Exception as e:
            logger.warning(f"⚠️ CoAP server failed: {e}")
    
    logger.info("🎉 Application startup complete!")
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🔴 Shutting down...")
    
    if app_state.coap_server:
        await app_state.coap_server.stop()
    
    if DATABASE_AVAILABLE and app_state.database_enabled:
        try:
            await close_db()
            logger.info("✅ Database closed")
        except Exception as e:
            logger.error(f"❌ Database close error: {e}")
    
    if DATABASE_AVAILABLE and app_state.redis_enabled:
        try:
            await close_redis()
            logger.info("✅ Redis closed")
        except Exception as e:
            logger.error(f"❌ Redis close error: {e}")
    
    logger.info("✅ Shutdown complete")

# Create FastAPI application
def create_application() -> FastAPI:
    """Create the FastAPI application"""
    
    app = FastAPI(
        title="Smart Greenhouse IoT System",
        description="Unified Smart Greenhouse IoT monitoring system with HTTP and CoAP support",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with system status"""
        return {
            "message": "Smart Greenhouse IoT System API",
            "version": "1.0.0",
            "status": "running",
            "mode": "database" if app_state.database_enabled else "simple",
            "services": {
                "database": app_state.database_enabled,
                "redis": app_state.redis_enabled,
                "coap": bool(app_state.coap_server and app_state.coap_server.running)
            },
            "endpoints": {
                "docs": "/docs",
                "health": "/health",
                "api_health": "/api/v1/health",
                "sensors": "/api/v1/sensors",
                "nodes": "/api/v1/nodes",
                "analytics": "/api/v1/analytics"
            }
        }
    
    # Health endpoints
    @app.get("/health")
    async def health_check():
        """Simple health check"""
        return {
            "status": "healthy",
            "service": "Smart Greenhouse IoT System",
            "version": "1.0.0"
        }
    
    @app.get("/api/v1/health")
    async def api_health():
        """Detailed API health check"""
        return {
            "status": "healthy",
            "version": "1.0.0",
            "api_version": "v1",
            "services": {
                "database": "connected" if app_state.database_enabled else "unavailable",
                "redis": "connected" if app_state.redis_enabled else "unavailable",
                "coap": "running" if (app_state.coap_server and app_state.coap_server.running) else "stopped"
            },
            "protocols": {
                "http": "http://localhost:8000",
                "coap": "coap://localhost:5683/sensor/send-data" if COAP_AVAILABLE else "unavailable"
            }
        }
    
    # Mock API endpoints (replace with real implementation when database is available)
    @app.get("/api/v1/sensors")
    async def list_sensors():
        """List all sensors"""
        # TODO: Implement database query when available
        return {
            "sensors": [
                {
                    "id": "sensor_001",
                    "node_id": "greenhouse_node_001",
                    "type": "soil_moisture",
                    "zone": "A1",
                    "status": "active",
                    "last_reading": "2025-08-01T10:30:00Z",
                    "value": 45.8
                },
                {
                    "id": "sensor_002",
                    "node_id": "greenhouse_node_001", 
                    "type": "temperature",
                    "zone": "A1",
                    "status": "active",
                    "last_reading": "2025-08-01T10:30:00Z",
                    "value": 22.5
                }
            ],
            "total": 2,
            "mode": "mock" if not app_state.database_enabled else "database"
        }
    
    @app.get("/api/v1/nodes")
    async def list_nodes():
        """List all nodes"""
        # TODO: Implement database query when available
        return {
            "nodes": [
                {
                    "id": "greenhouse_node_001",
                    "name": "Zone A1 Node",
                    "zone_id": "A1",
                    "status": "online",
                    "last_seen": "2025-08-01T10:30:00Z",
                    "battery_level": 85,
                    "sensor_count": 5,
                    "location": {"x": 10.5, "y": 5.2}
                }
            ],
            "total": 1,
            "mode": "mock" if not app_state.database_enabled else "database"
        }
    
    @app.get("/api/v1/analytics")
    async def get_analytics():
        """Get analytics data"""
        # TODO: Implement real analytics when database is available
        return {
            "overview": {
                "total_nodes": 1,
                "active_sensors": 2,
                "data_points_today": 1440,
                "system_uptime": "99.9%"
            },
            "soil_moisture": {"average": 45.8, "min": 35.2, "max": 58.1, "trend": "stable"},
            "temperature": {"average": 22.5, "min": 18.3, "max": 26.7, "trend": "rising"},
            "alerts": [],
            "mode": "mock" if not app_state.database_enabled else "database"
        }
    
    @app.post("/api/v1/sensors/data")
    async def receive_sensor_data(data: dict):
        """Receive sensor data from IoT devices"""
        logger.info(f"📊 HTTP sensor data received: {data}")
        # TODO: Save to database when available
        return {
            "status": "success",
            "message": "Data received via HTTP",
            "timestamp": "2025-08-01T10:30:00Z",
            "processed_readings": len(data.get("readings", []))
        }
    
    # Error handler
    @app.exception_handler(404)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not Found",
                "message": f"Endpoint {request.url.path} not found",
                "available_endpoints": ["/", "/health", "/docs", "/api/v1/health", "/api/v1/sensors", "/api/v1/nodes", "/api/v1/analytics"]
            }
        )
    
    return app

# Create application instance
app = create_application()

# Startup banner
def print_banner():
    """Print startup banner"""
    banner = f"""
╔═══════════════════════════════════════════════════════════════╗
║                 Smart Greenhouse IoT System                   ║
║                      Unified Backend                          ║
╠═══════════════════════════════════════════════════════════════╣
║ Version: 1.0.0                                               ║
║ HTTP API: http://localhost:8000                              ║
║ CoAP Server: {'coap://localhost:5683' if COAP_AVAILABLE else 'Disabled'}                           ║
║ Documentation: http://localhost:8000/docs                    ║
║ Mode: {'Database' if DATABASE_AVAILABLE else 'Simple'} Mode                                    ║
╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

if __name__ == "__main__":
    import uvicorn
    
    print_banner()
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    logger.info(f"🚀 Starting server on {host}:{port}")
    
    uvicorn.run(
        "main_unified:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )
